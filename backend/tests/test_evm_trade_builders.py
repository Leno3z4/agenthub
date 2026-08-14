import pytest
from web3 import Web3

from evm_swap import build_exact_input_single


class FakeEth:
    chain_id = 5042

    def get_transaction_count(self, address, block_identifier):
        return 7


class FakeWeb3:
    eth = FakeEth()


def test_swap_builder_rejects_missing_router():
    with pytest.raises(ValueError):
        build_exact_input_single(
            FakeWeb3(),
            "",
            "0x3600000000000000000000000000000000000000",
            "0x0000000000000000000000000000000000000001",
            3000,
            "0x0000000000000000000000000000000000000002",
            1,
            1,
        )
