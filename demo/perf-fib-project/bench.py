"""Benchmark gate for the Pawgress performance demo.

Exits 0 when fib(32) fits the time budget, 1 otherwise — so it can be used
directly as a Pawgress verify command.
"""

from __future__ import annotations

import argparse
import sys
import time

from fib import fib


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-ms", type=float, default=50.0)
    args = parser.parse_args()

    start = time.perf_counter()
    result = fib(32)
    elapsed_ms = (time.perf_counter() - start) * 1000

    if result != 2178309:
        print(f"FAIL fib(32) returned {result}, expected 2178309")
        return 1

    status = "PASS" if elapsed_ms <= args.max_ms else "FAIL"
    print(f"{status} fib(32) took {elapsed_ms:.1f}ms (budget {args.max_ms:.0f}ms)")
    return 0 if elapsed_ms <= args.max_ms else 1


if __name__ == "__main__":
    sys.exit(main())
