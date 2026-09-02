import hashlib
import json
import base64
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from cryptography.hazmat.primitives.asymmetric import ed25519

class StateTransition(BaseModel):
    step_id: str
    action: str
    resource: str
    previous_hash: str
    state_hash: str
    timestamp: str

class VerificationCertificate(BaseModel):
    context: List[str]
    certificate_id: str
    agent_id: str
    issuer: str
    public_key_hex: str
    issuance_date: str
    state_chain_root: str
    step_count: int
    signature: str
    steps: List[StateTransition]

class ExecutionVerifier:
    """
    Constructs hash-linked state transition chains during execution
    and produces W3C JSON-LD Verification Certificates signed via Ed25519.
    """
    def __init__(self, private_key_hex: Optional[str] = None):
        if private_key_hex:
            self._private_key = ed25519.Ed25519PrivateKey.from_private_bytes(bytes.fromhex(private_key_hex))
        else:
            self._private_key = ed25519.Ed25519PrivateKey.generate()
        self._public_key = self._private_key.public_key()
        self.public_key_hex = self._public_key.public_bytes_raw().hex()

    def get_public_key_multibase(self) -> str:
        raw_bytes = self._public_key.public_bytes_raw()
        return f"z{base64.b16encode(raw_bytes).decode().lower()}"

    def build_state_chain(self, agent_id: str, actions: List[Dict[str, Any]]) -> VerificationCertificate:
        steps: List[StateTransition] = []
        prev_hash = "0" * 64

        for idx, act in enumerate(actions):
            action_str = act.get("action", "")
            resource_str = act.get("resource", "")
            ts = act.get("timestamp") or datetime.now(timezone.utc).isoformat()

            raw_data = f"{idx}:{action_str}:{resource_str}:{prev_hash}:{ts}"
            current_hash = hashlib.sha256(raw_data.encode()).hexdigest()

            step = StateTransition(
                step_id=f"VRF-{idx+1:02d}",
                action=action_str,
                resource=resource_str,
                previous_hash=prev_hash,
                state_hash=current_hash,
                timestamp=ts
            )
            steps.append(step)
            prev_hash = current_hash

        # Root hash of execution chain
        root_hash = prev_hash
        cert_id = f"urn:uuid:{hashlib.sha256((agent_id + root_hash).encode()).hexdigest()[:16]}"
        now_ts = datetime.now(timezone.utc).isoformat()

        # Sign root hash + cert id
        payload_to_sign = f"{cert_id}|{agent_id}|{root_hash}|{len(steps)}|{now_ts}"
        sig_bytes = self._private_key.sign(payload_to_sign.encode())
        signature_hex = sig_bytes.hex()

        return VerificationCertificate(
            context=[
                "https://www.w3.org/2018/credentials/v1",
                "https://schema.avaira.io/trust/v1"
            ],
            certificate_id=cert_id,
            agent_id=agent_id,
            issuer=f"did:avaira:verifier:{hashlib.sha256(self.get_public_key_multibase().encode()).hexdigest()[:12]}",
            public_key_hex=self.public_key_hex,
            issuance_date=now_ts,
            state_chain_root=root_hash,
            step_count=len(steps),
            signature=signature_hex,
            steps=steps
        )

    def verify_certificate(self, cert: VerificationCertificate) -> bool:
        """
        Independently verifies state chain integrity and certificate signature.
        """
        if not cert.steps:
            return False

        # Re-verify state chain hash sequence
        prev_hash = "0" * 64
        for step in cert.steps:
            if step.previous_hash != prev_hash:
                return False
            step_num = int(step.step_id.replace("VRF-", "")) - 1
            raw_data = f"{step_num}:{step.action}:{step.resource}:{prev_hash}:{step.timestamp}"
            expected_hash = hashlib.sha256(raw_data.encode()).hexdigest()
            if step.state_hash != expected_hash:
                return False
            prev_hash = expected_hash

        if prev_hash != cert.state_chain_root:
            return False

        # Verify signature using public_key_hex from cert
        try:
            pub_key = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(cert.public_key_hex))
            payload_to_verify = f"{cert.certificate_id}|{cert.agent_id}|{cert.state_chain_root}|{cert.step_count}|{cert.issuance_date}"
            pub_key.verify(bytes.fromhex(cert.signature), payload_to_verify.encode())
            return True
        except Exception:
            return False
