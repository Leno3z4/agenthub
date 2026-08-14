import pytest
from web3 import Web3

from evm_client import PoolKey, normalize_address, pool_id


def test_normalize_address():
    address = "0x3600000000000000000000000000000000000000"
    assert normalize_address(address) == Web3.to_checksum_address(address)


def test_invalid_address():
    with pytest.raises(ValueError):
        normalize_address("not-an-address")


def test_pool_id_is_deterministic():
    pool = PoolKey(
        currency0="0x0000000000000000000000000000000000000001",
        currency1="0x0000000000000000000000000000000000000002",
        fee=3000,
        tick_spacing=60,
        hooks="0x0000000000000000000000000000000000000000",
    )

    first = pool_id(pool)
    second = pool_id(pool)

    assert first == second
    assert len(first) == 32
