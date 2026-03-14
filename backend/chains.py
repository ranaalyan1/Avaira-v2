from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class ChainConfig:
    key: str
    chain_id: int
    name: str
    rpc_url: str
    explorer_url: str
    contracts: Dict[str, str]


def _contracts_for(prefix: str) -> Dict[str, str]:
    def _value(name: str) -> str:
        scoped = os.environ.get(f"{prefix}_{name}", "").strip()
        if scoped:
            return scoped
        return os.environ.get(name, "").strip()

    return {
        "AGENT_REGISTRY_ADDRESS": _value("AGENT_REGISTRY_ADDRESS"),
        "EXECUTION_WALLET_ADDRESS": _value("EXECUTION_WALLET_ADDRESS"),
        "FREEZE_SLASH_ADDRESS": _value("FREEZE_SLASH_ADDRESS"),
        "TREASURY_ADDRESS": _value("TREASURY_ADDRESS"),
        "REPUTATION_ENGINE_ADDRESS": _value("REPUTATION_ENGINE_ADDRESS"),
        "INSURANCE_POOL_ADDRESS": _value("INSURANCE_POOL_ADDRESS"),
    }


SUPPORTED_CHAINS: Dict[int, ChainConfig] = {
    43113: ChainConfig(
        key="avalanche_fuji",
        chain_id=43113,
        name="Avalanche Fuji",
        rpc_url=os.environ.get("FUJI_RPC_URL", "https://api.avax-test.network/ext/bc/C/rpc").strip(),
        explorer_url="https://testnet.snowtrace.io",
        contracts=_contracts_for("FUJI"),
    ),
    11155111: ChainConfig(
        key="ethereum_sepolia",
        chain_id=11155111,
        name="Ethereum Sepolia",
        rpc_url=os.environ.get("SEPOLIA_RPC_URL", "").strip(),
        explorer_url="https://sepolia.etherscan.io",
        contracts=_contracts_for("SEPOLIA"),
    ),
    84531: ChainConfig(
        key="base_goerli",
        chain_id=84531,
        name="Base Goerli",
        rpc_url=os.environ.get("BASE_GOERLI_RPC_URL", "").strip(),
        explorer_url="https://goerli.basescan.org",
        contracts=_contracts_for("BASE_GOERLI"),
    ),
    421613: ChainConfig(
        key="arbitrum_goerli",
        chain_id=421613,
        name="Arbitrum Goerli",
        rpc_url=os.environ.get("ARBITRUM_GOERLI_RPC_URL", "").strip(),
        explorer_url="https://goerli.arbiscan.io",
        contracts=_contracts_for("ARBITRUM_GOERLI"),
    ),
}


def get_chain(chain_id: int) -> ChainConfig:
    if chain_id not in SUPPORTED_CHAINS:
        raise KeyError(f"Unsupported chain ID: {chain_id}")
    return SUPPORTED_CHAINS[chain_id]
