import hashlib
import uuid
import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

class TEEAttestation(BaseModel):
    enclave_id: str
    pcr0: str
    pcr1: str
    pcr2: str
    signature: str
    timestamp: str

class AvairaDID(BaseModel):
    did: str
    controller: str
    verification_method: Dict[str, Any]
    attestation: TEEAttestation

class TEEIdentityManager:
    """
    Manages Hardware-Anchored Identities (TEE-DIDs).
    Simulates AWS Nitro Enclave attestation for agent identity verification.
    """
    def __init__(self, secret: str = None):
        self.secret = secret or os.environ.get("TEE_SECRET", "hardware-root-of-trust-0x1337")

    def generate_agent_did(self, agent_id: str, public_key: str) -> AvairaDID:
        """
        Mints a new DID anchored in a hardware enclave attestation.
        """
        did = f"did:avaira:{agent_id}"
        timestamp = datetime.now(timezone.utc).isoformat()

        # Simulate PCR measurements (Hardware state measurements)
        pcr0 = hashlib.sha256(b"avaira-runtime-v2-core").hexdigest()
        pcr1 = hashlib.sha256(b"linux-kernel-nitro-5.15").hexdigest()
        pcr2 = hashlib.sha256(public_key.encode()).hexdigest()

        # Enclave Attestation Signature
        attestation_payload = f"{did}|{pcr0}|{pcr1}|{pcr2}|{timestamp}"
        signature = hashlib.sha3_256((attestation_payload + self.secret).encode()).hexdigest()

        attestation = TEEAttestation(
            enclave_id=f"nitro-{uuid.uuid4().hex[:12]}",
            pcr0=pcr0,
            pcr1=pcr1,
            pcr2=pcr2,
            signature=signature,
            timestamp=timestamp
        )

        return AvairaDID(
            did=did,
            controller=f"did:avaira:controller",
            verification_method={
                "id": f"{did}#key-1",
                "type": "Ed25519VerificationKey2020",
                "controller": did,
                "publicKeyMultibase": public_key
            },
            attestation=attestation
        )

    def verify_attestation(self, did_doc: AvairaDID) -> bool:
        """
        Verifies that the DID was indeed minted inside a valid TEE with strict schema validation.
        """
        att = did_doc.attestation

        # Strict JSON Schema / Format validation
        if not att.enclave_id or not att.enclave_id.startswith("nitro-"):
            return False
        if len(att.pcr0) != 64 or len(att.pcr1) != 64 or len(att.pcr2) != 64:
            return False
        if len(att.signature) != 64:
            return False

        # Validate timestamp freshness / ISO 8601 format
        try:
            att_dt = datetime.fromisoformat(att.timestamp)
            # Timestamp must be in past or within acceptable skew (300 seconds)
            now = datetime.now(timezone.utc)
            if att_dt > now and (att_dt - now).total_seconds() > 300:
                return False
        except (ValueError, TypeError):
            return False

        payload = f"{did_doc.did}|{att.pcr0}|{att.pcr1}|{att.pcr2}|{att.timestamp}"
        expected_sig = hashlib.sha3_256((payload + self.secret).encode()).hexdigest()

        known_pcr0 = hashlib.sha256(b"avaira-runtime-v2-core").hexdigest()

        return (expected_sig == att.signature) and (att.pcr0 == known_pcr0)
