import hashlib
import os
from typing import List, Dict, Any
from pydantic import BaseModel
from cryptography.hazmat.primitives.asymmetric import ed25519

class WitnessSignature(BaseModel):
    witness_id: str
    witness_name: str
    signature: str
    timestamp: str

class WitnessNetwork:
    """
    Simulates a decentralized network of neutral witnesses (regulators, universities).
    Used to co-sign agent audit trail anchor points.
    """
    def __init__(self):
        self.witnesses = [
            {"id": "did:avaira:witness:mit", "name": "MIT CSAIL Trust Lab"},
            {"id": "did:avaira:witness:finra", "name": "Financial Integrity Monitor"},
            {"id": "did:avaira:witness:standard", "name": "Open Accountability Foundation"}
        ]
        # Fixed simulation keys
        self.witness_keys = {
            w["id"]: ed25519.Ed25519PrivateKey.from_private_bytes(hashlib.sha256(w["id"].encode()).digest())
            for w in self.witnesses
        }

    async def co_sign_anchor(self, merkle_root: str, timestamp: str) -> List[WitnessSignature]:
        """
        Request signatures from a quorum of witnesses for a Merkle root.
        """
        signatures = []
        # In a real system, this would be an async p2p broadcast / RPC call.
        for w in self.witnesses:
            sk = self.witness_keys[w["id"]]
            payload = f"{merkle_root}|{timestamp}".encode()
            sig = sk.sign(payload).hex()
            signatures.append(WitnessSignature(
                witness_id=w["id"],
                witness_name=w["name"],
                signature=sig,
                timestamp=timestamp
            ))
        return signatures

    def verify_witness_signature(self, merkle_root: str, timestamp: str, witness_sig: WitnessSignature) -> bool:
        try:
            sk = self.witness_keys.get(witness_sig.witness_id)
            if not sk: return False
            pk = sk.public_key()
            payload = f"{merkle_root}|{timestamp}".encode()
            pk.verify(bytes.fromhex(witness_sig.signature), payload)
            return True
        except Exception:
            return False
