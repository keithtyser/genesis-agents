"""
cli.sandbox – command-line entry point for the empty-earth simulation.

Usage
-----
    python -m cli.sandbox --ticks 100
"""

from __future__ import annotations
import argparse, asyncio, sys
from pathlib import Path

from sandbox.world     import WorldState
from sandbox.scheduler import build_default

def main():
    # -------- argument parsing ------------
    p = argparse.ArgumentParser(
        prog="python -m cli.sandbox",
        description="Run the sandbox simulation for a fixed number of ticks.",
    )
    p.add_argument("--ticks", type=int, default=100,
                   help="number of ticks to run (default 100)")
    p.add_argument("--world", default="world.json",
                   help="path to world.json (default ./world.json)")
    args = p.parse_args()

    # -------- load world file -------------
    world_path = Path(args.world)
    world      = WorldState.load(str(world_path))

    # -------- build scheduler -------------
    sched      = build_default(world)

    # -------- run loop --------------------
    try:
        asyncio.run(sched.loop(max_ticks=args.ticks))
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        world.save(str(world_path))
        print(f"World saved to {world_path.resolve()}")

if __name__ == "__main__":
    main() 