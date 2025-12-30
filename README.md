# GPU Zombie Hunter

Finds GPU processes that are holding memory but doing zero work.

## The Problem
When training jobs crash, they often leave "zombie" processes behind. These processes hold onto GPU memory but use 0% compute. On cloud GPUs (H100/A100), this wastes thousands of dollars per month.

## What This Tool Does
1. Samples GPU utilization multiple times (to avoid false positives)
2. Flags processes with High Memory + Low Utilization
3. Calculates potential wasted money
4. Gives you the command to manually verify

## Usage
No dependencies required.

1. Clone the repo
2. Run: `python main.py`

### Options
- `python main.py --explain` (Shows how detection works)
- `python main.py --mock` (Runs with fake data for testing)
- `python main.py --mem-threshold 2000` (Sets memory threshold to 2GB)

## Safety
- Read-only (uses nvidia-smi)
- Never kills processes automatically
- Conservative detection (checks multiple samples)

## License
MIT

