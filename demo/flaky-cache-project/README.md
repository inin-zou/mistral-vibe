# Flaky Cache — Pawgress demo project

A deliberately-broken `LRUCache` for demoing the Pawgress persistent-goal runtime:
**verify fails → the agent keeps working → verify eventually passes 5/5.**

## The goal to type

```
/pawgress "Fix the failing cache test" --verify "pytest test_cache.py" --repeat 5
```

Pawgress re-runs `pytest test_cache.py` 5 times per verification pass. While the
bug is present the tests fail deterministically (0/5); after the one-line fix
they pass deterministically (5/5).

## The bug

In `cache.py`, `LRUCache.put` evicts the **most**-recently-used entry when the
cache is over capacity:

```python
self._store.popitem(last=True)   # evicts MRU — wrong
```

`test_evicts_least_recently_used_entry` and `test_capacity_is_never_exceeded`
both fail because the wrong entries get thrown away.

## The fix (one line)

Evict the **least**-recently-used entry instead:

```python
self._store.popitem(last=False)  # evicts LRU — correct
```

## Run it manually

```
cd demo/flaky-cache-project
pytest test_cache.py            # fails with the bug present
# apply the fix above
pytest test_cache.py            # passes
```

Self-contained: standard library + pytest only.
