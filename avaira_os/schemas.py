"""Avaira Cognitive OS v5.0 — strict schema layer.

Every object that crosses a pillar boundary (plan, trace, certificate,
attestation, artifact, verdict) is a frozen Pydantic model. Nothing in the
kernel trusts an untyped dict: fail-closed starts at the type system.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import math
from enum import Enum
from typing import Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ---------------------------------------------------------------------------
# Verdicts
# ---------------------------------------------------------------------------


class Verdict(str, Enum):
    """Proof-of-Safety verdict. UNKNOWN is a fail-closed outcome."""

    SAFE = "SAFE"
    UNSAFE = "UNSAFE"
    UNKNOWN = "UNKNOWN"


class OSState(str, Enum):
    IDLE = "IDLE"
    PLANNING = "PLANNING"
    PROVING = "PROVING"
    SIMULATING = "SIMULATING"
    EXECUTING = "EXECUTING"
    AWAIT_INPUT = "AWAIT_INPUT"
    COMPLETED = "COMPLETED"
    REFUSED = "REFUSED"
    SLASHED = "SLASHED"
    ABORTED = "ABORTED"


# ---------------------------------------------------------------------------
# Plans
# ---------------------------------------------------------------------------


class ParamBound(BaseModel):
    """Interval of admissible values for one step parameter.

    Symbolic execution propagates the *interval*; the Monte-Carlo sandbox
    samples uniformly inside it.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    lo: float
    hi: float

    @field_validator("lo", "hi")
    @classmethod
    def _finite(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("parameter bounds must be finite")
        return v

    def __init__(self, **data: object) -> None:
        lo, hi = data.get("lo", 0.0), data.get("hi", 0.0)
        if lo > hi:  # normalize instead of failing: an inverted interval is ambiguous
            data["lo"], data["hi"] = min(lo, hi), max(lo, hi)
        super().__init__(**data)


class EffectKind(str, Enum):
    """Whitelisted effect algebra of the symbolic prover.

    Anything outside this algebra cannot be proven and yields UNKNOWN
    (fail-closed) rather than a guess.
    """

    SPEND = "spend"    # variable -= amount  (and total_spend += amount)
    CREDIT = "credit"  # variable += amount
    SET = "set"        # variable := amount


class Effect(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: EffectKind
    variable: str
    # name of the step parameter whose bound supplies the amount
    amount_param: str


class PlanStep(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    action: str
    params: Dict[str, ParamBound]
    effects: List[Effect] = Field(default_factory=list)
    description: str = ""

    def amount_of(self, effect: Effect) -> ParamBound:
        if effect.amount_param not in self.params:
            raise KeyError(f"step '{self.id}' effect references missing param '{effect.amount_param}'")
        return self.params[effect.amount_param]


class Critique(BaseModel):
    """Carried on the back-edge PLAN<-PROVE/SIMULATE."""

    origin: Literal["prover", "sandbox", "gate", "rules"]
    reason: str
    iteration: int = 0
    witness: Optional["Witness"] = None


class ReasoningTrace(BaseModel):
    """System-2 trace: mandatory before any plan may be emitted."""

    model_config = ConfigDict(frozen=True)

    decomposition: List[str] = Field(default_factory=list)
    risk_analysis: List[str] = Field(default_factory=list)
    alternatives: List[str] = Field(default_factory=list)
    decision: str = ""

    def is_complete(self) -> bool:
        return bool(self.decomposition) and bool(self.risk_analysis) and bool(self.alternatives) and bool(self.decision)


class Plan(BaseModel):
    model_config = ConfigDict(frozen=True)

    goal: str
    steps: List[PlanStep] = Field(default_factory=list)
    trace: ReasoningTrace
    critique: Optional[Critique] = None
    iteration: int = 0

    def plan_hash(self) -> str:
        return sha256_canonical(self.model_dump())

    def total_cost_hi(self) -> float:
        """Worst-case total spend across all steps (upper interval bound)."""
        total = 0.0
        for step in self.steps:
            for effect in step.effects:
                if effect.kind == EffectKind.SPEND:
                    total += step.amount_of(effect).hi
        return round(total, 10)


# ---------------------------------------------------------------------------
# Proof-of-Safety outputs
# ---------------------------------------------------------------------------


class Witness(BaseModel):
    """Concrete counterexample proving UNSAFE."""

    model_config = ConfigDict(frozen=True)

    step_id: str
    variable: str
    breach: Literal["above_hi", "below_lo"]
    observed_interval: Tuple[float, float]
    hard_bound: Tuple[float, float]
    params: Dict[str, float]  # concrete parameter assignment that triggers it


class ProofResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    verdict: Verdict
    reason: str
    witness: Optional[Witness] = None
    final_state: Dict[str, Tuple[float, float]] = Field(default_factory=dict)
    prover_version: str = "interval-symbolic-v5.0"


class SandboxResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    runs: int
    violations: int
    confidence: float
    seed: int
    simulator_version: str = "shadow-montecarlo-v5.0"


# ---------------------------------------------------------------------------
# Certificates & attestation
# ---------------------------------------------------------------------------


class SafetyCertificate(BaseModel):
    """Signed proof artifact: no certificate, no execution. Ever."""

    model_config = ConfigDict(frozen=True)

    plan_hash: str
    verdict: Verdict = Verdict.SAFE
    prover_version: str = "interval-symbolic-v5.0"
    nonce: str
    issued_tick: int
    signature: str = ""

    def signing_payload(self) -> str:
        return f"{self.plan_hash}|{self.verdict.value}|{self.nonce}|{self.issued_tick}"

    def sign(self, key: str) -> "SafetyCertificate":
        mac = hmac.new(key.encode(), self.signing_payload().encode(), hashlib.sha256).hexdigest()
        return self.model_copy(update={"signature": mac})

    def verify(self, key: str) -> bool:
        if not self.signature:
            return False
        expected = hmac.new(key.encode(), self.signing_payload().encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, self.signature)


class TEEAttestation(BaseModel):
    """Simulated AWS-Nitro-style attestation (deterministic, offline).

    PCR0 is the measurement of the Cognitive OS runtime image; the enclave
    signs (identity | PCRs | nonce) with a key derived from the root secret.
    """

    model_config = ConfigDict(frozen=True)

    agent_id: str
    enclave_id: str
    pcr0: str
    pcr1: str
    pcr2: str
    nonce: str
    signature: str = ""

    def signing_payload(self) -> str:
        return f"{self.agent_id}|{self.pcr0}|{self.pcr1}|{self.pcr2}|{self.nonce}"

    def sign(self, secret: str) -> "TEEAttestation":
        sig = hashlib.sha3_256((self.signing_payload() + secret).encode()).hexdigest()
        return self.model_copy(update={"signature": sig})

    def verify(self, secret: str, expected_pcr0: str) -> bool:
        if not self.signature:
            return False
        expected_sig = hashlib.sha3_256((self.signing_payload() + secret).encode()).hexdigest()
        return hmac.compare_digest(expected_sig, self.signature) and self.pcr0 == expected_pcr0


# ---------------------------------------------------------------------------
# Verification artifacts (proof-gated memory writes)
# ---------------------------------------------------------------------------


class ArtifactType(str, Enum):
    SAFETY_CERTIFICATE = "safety_certificate"
    HUMAN_HASH = "human_hash"
    EXECUTION_AUDIT = "execution_audit"


class VerificationArtifact(BaseModel):
    """Evidence that a belief is backed by something stronger than vibes."""

    model_config = ConfigDict(frozen=True)

    type: ArtifactType
    ref: str          # hash / id of the backing evidence
    source: str       # independent origin tag, used for corroboration independence

    def is_valid(self) -> bool:
        return bool(self.ref) and bool(self.source)


# ---------------------------------------------------------------------------
# Envelope
# ---------------------------------------------------------------------------


class Bound(BaseModel):
    model_config = ConfigDict(frozen=True)

    lo: float
    hi: float

    def contains(self, value: float) -> bool:
        return self.lo <= value <= self.hi

    def as_tuple(self) -> Tuple[float, float]:
        return (self.lo, self.hi)


class Envelope(BaseModel):
    """Hard-rule boundaries. The prover proves the plan stays inside these."""

    model_config = ConfigDict(frozen=True)

    cost_cap_usd: float = 100.0
    allowed_actions: List[str] = Field(default_factory=list)
    # state variable -> hard interval that must hold after every step
    hard_bounds: Dict[str, Bound] = Field(default_factory=dict)
    max_steps: int = 12

    def bound_of(self, variable: str) -> Optional[Bound]:
        return self.hard_bounds.get(variable)


# ---------------------------------------------------------------------------
# Execution audit
# ---------------------------------------------------------------------------


class ExecutionAudit(BaseModel):
    model_config = ConfigDict(frozen=True)

    audit_id: str
    plan_hash: str
    status: Literal["completed", "refused", "aborted"]
    final_state: Dict[str, float] = Field(default_factory=dict)
    steps_executed: int = 0


# ---------------------------------------------------------------------------
# Canonical hashing helpers
# ---------------------------------------------------------------------------


def canonical_json(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def sha256_canonical(data: object) -> str:
    return hashlib.sha256(canonical_json(data).encode()).hexdigest()
