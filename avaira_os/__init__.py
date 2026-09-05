"""Avaira Cognitive OS v5.0 — a Hardened Execution Layer for AI agents.

Pillars:
  A  Cognitive Kernel      — kernel.py, reasoning.py
  B  Virtual Memory        — memory_tiers.py
  C  World Model & Proof   — world_model.py
  D  Hardened Execution    — execution_gate.py
  E  Loop Orchestration    — agent_os.py, events.py

Every action carries a signed safety certificate; every transition is
hash-chained; every gate refusal is fail-closed.
"""
from .agent_os import AgentOS, OSResult
from .events import CognitiveLedger, EventBus, Event, EventType
from .execution_gate import (AttestationService, EVMFreezeSlashAdapter,
                             ExecutionGate, LocalLedgerSlashing, RefusalReason)
from .kernel import Chunk, ChunkKind, GlobalWorkingMemory, InterruptSignal, ProductionRule, RuleEngine
from .memory_tiers import Belief, BeliefGraph, EpisodicStore, SelfEditingMemory, WriteDecision
from .reasoning import AmbiguityError, PlanningRefused, System2Planner, TraceRequired
from .schemas import (ArtifactType, Bound, Critique, Effect, EffectKind,
                      Envelope, ExecutionAudit, OSState, ParamBound, Plan,
                      PlanStep, ProofResult, ReasoningTrace, SafetyCertificate,
                      SandboxResult, TEEAttestation, VerificationArtifact,
                      Verdict, Witness)
from .world_model import Interval, ShadowSandbox, SymbolicProver

__version__ = "5.0.0"

__all__ = [
    "AgentOS", "OSResult",
    "CognitiveLedger", "EventBus", "Event", "EventType",
    "AttestationService", "EVMFreezeSlashAdapter", "ExecutionGate",
    "LocalLedgerSlashing", "RefusalReason",
    "Chunk", "ChunkKind", "GlobalWorkingMemory", "InterruptSignal",
    "ProductionRule", "RuleEngine",
    "Belief", "BeliefGraph", "EpisodicStore", "SelfEditingMemory", "WriteDecision",
    "AmbiguityError", "PlanningRefused", "System2Planner", "TraceRequired",
    "ArtifactType", "Bound", "Critique", "Effect", "EffectKind", "Envelope",
    "ExecutionAudit", "OSState", "ParamBound", "Plan", "PlanStep", "ProofResult",
    "ReasoningTrace", "SafetyCertificate", "SandboxResult", "TEEAttestation",
    "VerificationArtifact", "Verdict", "Witness",
    "Interval", "ShadowSandbox", "SymbolicProver",
    "__version__",
]
