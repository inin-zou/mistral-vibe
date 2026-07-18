"""Fibonacci helpers used for the Pawgress performance-goal demo.

It is deliberately slow (see README.md) so a coding agent can optimize it live
while Pawgress re-runs the benchmark until it fits the time budget.
"""

from __future__ import annotations


def fib(n: int) -> int:
    # SLOW: recomputes the same subproblems exponentially. The one-line fix is
    # memoization (e.g. functools.lru_cache) or an iterative loop.
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)
