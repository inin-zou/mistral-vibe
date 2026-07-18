# Pawgress performance-goal demo

A tiny project whose `fib()` is deliberately exponential. The benchmark fails
until the agent optimizes it (memoization / iteration), then passes with a
massive margin — a reliable live demo of an evidence-driven *performance* goal.

## Run the demo

```bash
cd demo/perf-fib-project
uv run vibe
```

Then inside Vibe:

```
/pawgress "Make fib(32) run under 50ms" --verify "python bench.py --max-ms 50 && python -m pytest test_fib.py -o addopts='' -q" --repeat 3
```

- With the slow implementation: `bench.py` prints `FAIL fib(32) took ~135ms` →
  verification 0/3 → Pawgress auto-continues.
- After the fix (`functools.lru_cache` on `fib`, or an iterative loop):
  `PASS fib(32) took ~0.0ms` → 3/3 → goal complete, correctness tests still
  green.

## The intended fix

```python
from functools import lru_cache

@lru_cache(maxsize=None)
def fib(n: int) -> int:
    ...
```

Keep the repo in the SLOW state for the live demo (`git checkout fib.py` after
rehearsals).
