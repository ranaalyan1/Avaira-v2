"""
Chain configuration for AVAIRA Protocol.
Single source of truth for all network parameters.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from enum import IntEnum
from typing import Dict


class ChainId(IntEnum):
    HARDHAT = 31337
    FUJI = 43113
    MAINNET = 43114


@dataclass(frozen=True)
class ChainConfig:
    key: str
    chain_id: int
    name: str
    rpc_url: str
    explorer_url: str
    explorer_api_url: str
    native_currency: str
    contracts: Dict[str, str]


def _contracts_for(prefix: str) -> Dict[str, str]:
    def _value(name: str) -> str:
        scoped = os.environ.get(f"{prefix}_{name}", "").strip()
        return scoped or os.environ.get(name, "").strip()

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
        name="Avalanche Fuji Testnet",
        rpc_url=os.environ.get("FUJI_RPC_URL", "https://api.avax-test.network/ext/bc/C/rpc").strip(),
        explorer_url="https://testnet.snowtrace.io",
        explorer_api_url="https://api-testnet.snowtrace.io/api",
        native_currency="AVAX",
        contracts=_contracts_for("FUJI"),
    ),
    43114: ChainConfig(
        key="avalanche_mainnet",
        chain_id=43114,
        name="Avalanche C-Chain Mainnet",
        rpc_url=os.environ.get("MAINNET_RPC_URL", "https://api.avax.network/ext/bc/C/rpc").strip(),
        explorer_url="https://snowtrace.io",
        explorer_api_url="https://api.snowtrace.io/api",
        native_currency="AVAX",
        contracts=_contracts_for("MAINNET"),
    ),
    11155111: ChainConfig(
        key="ethereum_sepolia",
        chain_id=11155111,
        name="Ethereum Sepolia",
        rpc_url=os.environ.get("SEPOLIA_RPC_URL", "").strip(),
        explorer_url="https://sepolia.etherscan.io",
        explorer_api_url="https://api-sepolia.etherscan.io/api",
        native_currency="ETH",
        contracts=_contracts_for("SEPOLIA"),
    ),
    84532: ChainConfig(
        key="base_sepolia",
        chain_id=84532,
        name="Base Sepolia",
        rpc_url=os.environ.get("BASE_SEPOLIA_RPC_URL", "").strip(),
        explorer_url="https://sepolia.basescan.org",
        explorer_api_url="https://api-sepolia.basescan.org/api",
        native_currency="ETH",
        contracts=_contracts_for("BASE_SEPOLIA"),
    ),
    421614: ChainConfig(
        key="arbitrum_sepolia",
        chain_id=421614,
        name="Arbitrum Sepolia",
        rpc_url=os.environ.get("ARBITRUM_SEPOLIA_RPC_URL", "").strip(),
        explorer_url="https://sepolia.arbiscan.io",
        explorer_api_url="https://api-sepolia.arbiscan.io/api",
        native_currency="ETH",
        contracts=_contracts_for("ARBITRUM_SEPOLIA"),
    ),
}


def get_chain(chain_id: int) -> ChainConfig:
    if chain_id not in SUPPORTED_CHAINS:
        raise KeyError(f"Unsupported chain ID: {chain_id}")
    return SUPPORTED_CHAINS[chain_id]
