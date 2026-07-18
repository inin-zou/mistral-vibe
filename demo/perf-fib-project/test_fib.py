from __future__ import annotations

from fib import fib


def test_base_cases() -> None:
    assert fib(0) == 0
    assert fib(1) == 1


def test_known_values() -> None:
    assert fib(10) == 55
    assert fib(20) == 6765
