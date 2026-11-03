import asyncio

import pytest

from cashu.core.base import BlindedSignature, Proof, Unit
from cashu.core.helpers import (
    amount_summary,
    async_unwrap,
    async_wrap,
    fee_reserve,
    sum_promises,
    sum_proofs,
)
from cashu.core.settings import settings


def _proof(amount: int) -> Proof:
    return Proof(id="009a1f293253e41e", amount=amount, secret="s", C="c")


def _promise(amount: int) -> BlindedSignature:
    return BlindedSignature(id="009a1f293253e41e", amount=amount, C_="02aa")


def test_amount_summary_groups_and_sorts_amounts():
    proofs = [_proof(8), _proof(1), _proof(8), _proof(2)]
    assert amount_summary(proofs, Unit.sat) == "1 sat (1x), 2 sat (1x), 8 sat (2x)"


def test_amount_summary_uses_unit_formatting():
    proofs = [_proof(100), _proof(100)]
    assert amount_summary(proofs, Unit.usd) == "$1.00 USD (2x)"


def test_amount_summary_empty():
    assert amount_summary([], Unit.sat) == ""


def test_sum_proofs():
    assert sum_proofs([_proof(1), _proof(2), _proof(8)]) == 11
    assert sum_proofs([]) == 0


def test_sum_promises():
    assert sum_promises([_promise(4), _promise(16)]) == 20
    assert sum_promises([]) == 0


def test_fee_reserve_uses_minimum(monkeypatch):
    monkeypatch.setattr(settings, "lightning_reserve_fee_min", 2000)
    monkeypatch.setattr(settings, "lightning_fee_percent", 1.0)
    # 1% of 100_000 msat is 1000 msat, below the 2000 msat minimum
    assert fee_reserve(100_000) == 2000


def test_fee_reserve_uses_percentage(monkeypatch):
    monkeypatch.setattr(settings, "lightning_reserve_fee_min", 2000)
    monkeypatch.setattr(settings, "lightning_fee_percent", 1.0)
    # 1% of 1_000_000 msat is 10_000 msat, above the 2000 msat minimum
    assert fee_reserve(1_000_000) == 10_000


@pytest.mark.asyncio
async def test_async_wrap_runs_function_and_passes_arguments():
    def add(a, b=0):
        return a + b

    wrapped = async_wrap(add)
    assert await wrapped(1, b=2) == 3


@pytest.mark.asyncio
async def test_async_wrap_preserves_function_name():
    def my_function():
        return None

    assert async_wrap(my_function).__name__ == "my_function"


@pytest.mark.asyncio
async def test_async_wrap_propagates_exceptions():
    def boom():
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        await async_wrap(boom)()


def test_async_unwrap_returns_awaited_result():
    async def coro():
        return 42

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        assert async_unwrap(coro()) == 42
    finally:
        asyncio.set_event_loop(None)
        loop.close()
