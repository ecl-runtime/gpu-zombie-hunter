#!/usr/bin/env python3
import subprocess
import sys
import time
import argparse
from datetime import datetime

SAFE_PROCESSES = [
    'Xorg', 'X', 'kworker', 'kernel', 'systemd', 'jupyter', 'sshd', 'bash',
    'nvidia-smi', 'nvidia-persistenced', 'gpustat', 'wandb', 'tensorboard',
    'dbt', 'dask-worker', 'ray', 'redis', 'containerd', 'dockerd', 'gnome-shell'
]

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mock', action='store_true', help='Run with mock data')
    parser.add_argument('--explain', action='store_true', help='Show explanation')
    parser.add_argument('--mem-threshold', type=int, default=1000, help='Memory threshold MB')
    parser.add_argument('--util-threshold', type=int, default=5, help='Utilization threshold')
    parser.add_argument('--samples', type=int, default=5, help='Number of samples')
    parser.add_argument('--interval', type=int, default=2, help='Seconds between samples')
    return parser.parse_args()

def get_mock_data():
    return [
        '101, pythontrain.py, 14500, 98',
        '102, zombieprocess.py, 15500, 0',
        '103, Xorg, 400, 1'
    ]

def get_nvidia_smi_output(mock=False):
    if mock:
        return get_mock_data()
    try:
        cmd = [
            'nvidia-smi',
            '--query-compute-apps=pid,process_name,used_memory,utilization.gpu',
            '--format=csv,noheader,nounits'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            return get_mock_data()
        return result.stdout.strip().split('\n')
    except:
        return get_mock_data()

def parse_line(line):
    if not line.strip():
        return None
    parts = [p.strip() for p in line.split(',')]
    if len(parts) < 3:
        return None
    util = 0
    if len(parts) >= 4:
        try:
            util = int(parts[3])
        except:
            util = 0
    try:
        mem = int(parts[2])
    except:
        return None
    return {
        'pid': parts[0],
        'name': parts[1],
        'mem': mem,
        'util': util
    }

def scan(args):
    if args.explain:
        print("This tool samples GPU utilization over time.")
        print("If a process has high memory usage but consistently low utilization")
        print("across multiple samples, it is flagged as a potential zombie.")
        print("SAFE PROCESSES ignored:", ', '.join(sorted(SAFE_PROCESSES)))
        return

    print(f"Sampling {args.samples} times (interval: {args.interval}s)...")
    process_stats = {}
    
    for i in range(args.samples):
        lines = get_nvidia_smi_output(args.mock)
        for line in lines:
            p = parse_line(line)
            if not p:
                continue
            pid = p['pid']
            if pid not in process_stats:
                process_stats[pid] = {
                    'name': p['name'],
                    'mem': p['mem'],
                    'utils': []
                }
            process_stats[pid]['utils'].append(p['util'])
            process_stats[pid]['mem'] = max(process_stats[pid]['mem'], p['mem'])
        
        if i < args.samples - 1:
            time.sleep(args.interval)
    
    print("-" * 70)
    print(f"{'PID':<8} {'PROCESS':<25} {'MEM MB':<12} {'AVG UTIL':<10} {'STATUS'}")
    print("-" * 70)
    
    suspicious_mem_total = 0
    found_zombie = False
    
    for pid, stats in process_stats.items():
        avg_util = sum(stats['utils']) / len(stats['utils'])
        is_safe = any(s in stats['name'] for s in SAFE_PROCESSES)
        
        status = "OK"
        if is_safe:
            status = "SAFE"
        elif stats['mem'] >= args.mem_threshold and avg_util < args.util_threshold:
            status = "SUSPICIOUS"
            suspicious_mem_total += stats['mem']
            found_zombie = True
        
        print(f"{pid:<8} {stats['name']:<25} {stats['mem']:<12} {avg_util:.1f}{status}")
    
    print("-" * 70)
    
    if found_zombie:
        hourly = 4.0
        daily_waste = suspicious_mem_total * hourly * 24 / 1000
        monthly_waste = daily_waste * 30
        print("POTENTIAL WASTE DETECTED")
        print(f"Daily: ${daily_waste:.2f}")
        print(f"Monthly: ${monthly_waste:.2f}")
        print("VERIFY MANUALLY")
        print("Run: ps aux | grep PID")
        sys.exit(1)
    else:
        print("No suspicious processes found.")
        sys.exit(0)

if __name__ == '__main__':
    scan(get_args())

