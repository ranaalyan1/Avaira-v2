from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict

from eth_account import Account
from eth_account.messages import encode_typed_data
from eth_utils.address import to_checksum_address
from eth_utils.crypto import keccak


ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def _secret_to_private_key(secret: str) -> str:
    normalized = secret.strip()
    if not normalized:
        raise RuntimeError("PERMIT_SECRET is not configured")
    if normalized.startswith("0x") and len(normalized) == 66:
        return normalized
    return f"0x{keccak(text=normalized).hex()}"


def _signing_private_key() -> str:
    explicit = os.environ.get("PERMIT_PRIVATE_KEY", "").strip()
    if explicit.startswith("0x") and len(explicit) == 66:
        return explicit

    protocol_key = os.environ.get("PROTOCOL_PRIVATE_KEY", "").strip()
    if protocol_key.startswith("0x") and len(protocol_key) == 66:
        return protocol_key

    return _secret_to_private_key(os.environ.get("PERMIT_SECRET", ""))


def _permit_signer():
    return Account.from_key(_signing_private_key())


def _value_to_wei(value: float | int | str | Decimal) -> int:
    decimal_value = Decimal(str(value))
    return int(decimal_value * Decimal(10**18))


def _typed_data(agent_address: str, action: str, target: str, value_wei: int, nonce: int, deadline: int, chain_id: int) -> Dict[str, Any]:
    verifying_contract = os.environ.get("EXECUTION_WALLET_ADDRESS", ZERO_ADDRESS) or ZERO_ADDRESS
    return {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
            ],
            "ExecutionPermit": [
                {"name": "agent", "type": "address"},
                {"name": "action", "type": "string"},
                {"name": "target", "type": "address"},
                {"name": "value", "type": "uint256"},
                {"name": "nonce", "type": "uint256"},
                {"name": "deadline", "type": "uint256"},
            ],
        },
        "primaryType": "ExecutionPermit",
        "domain": {
            "name": "AvairaProtocol",
            "version": "1",
            "chainId": chain_id,
            "verifyingContract": to_checksum_address(verifying_contract),
        },
        "message": {
            "agent": to_checksum_address(agent_address),
            "action": action,
            "target": to_checksum_address(target),
            "value": value_wei,
            "nonce": nonce,
            "deadline": deadline,
        },
    }


def generate_permit(agent_address: str, action: str, target: str, value: float | int | str, nonce: int, chain_id: int = 43113) -> Dict[str, Any]:
    deadline = int((datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp())
    typed_data = _typed_data(agent_address, action, target, _value_to_wei(value), nonce, deadline, chain_id)
    signable = encode_typed_data(full_message=typed_data)
    signed = Account.sign_message(signable, _signing_private_key())
    return {
        "permit": typed_data["message"],
        "signature": signed.signature.hex(),
        "deadline": deadline,
        "signer": _permit_signer().address,
        "typed_data": typed_data,
    }


def verify_permit(permit: Dict[str, Any], signature: str, agent_address: str) -> bool:
    typed_data = {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
            ],
            "ExecutionPermit": [
                {"name": "agent", "type": "address"},
                {"name": "action", "type": "string"},
                {"name": "target", "type": "address"},
                {"name": "value", "type": "uint256"},
                {"name": "nonce", "type": "uint256"},
                {"name": "deadline", "type": "uint256"},
            ],
        },
        "primaryType": "ExecutionPermit",
        "domain": {
            "name": "AvairaProtocol",
            "version": "1",
            "chainId": int(permit.get("chainId", 43113) or 43113),
            "verifyingContract": to_checksum_address(permit.get("verifyingContract") or os.environ.get("EXECUTION_WALLET_ADDRESS", ZERO_ADDRESS) or ZERO_ADDRESS),
        },
        "message": {
            "agent": to_checksum_address(permit["agent"]),
            "action": permit["action"],
            "target": to_checksum_address(permit["target"]),
            "value": int(permit["value"]),
            "nonce": int(permit["nonce"]),
            "deadline": int(permit["deadline"]),
        },
    }
    signable = encode_typed_data(full_message=typed_data)
    recovered = Account.recover_message(signable, signature=signature)
    accepted_signers = {
        to_checksum_address(agent_address).lower(),
        _permit_signer().address.lower(),
    }
    return recovered.lower() in accepted_signers