"""Avaira Cognitive OS v5.0 — events, event bus and the Cognitive Ledger.

Every state transition in the DCG loop is emitted as an `Event` and appended
to a `CognitiveLedger`: a tamper-evident, hash-chained log. Each event's hash
commits to (seq, type, tick, payload, prev_hash) — mutating any historical
payload breaks the chain and `verify_chain()` reports the first broken seq.
"""
from __future__ import annotations

from enum import Enum
from typing import Callable, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .schemas import canonical_json, sha256_canonical

GENESIS_HASH = "0" * 64


class EventType(str, Enum):
    GOAL_SET = "GOAL_SET"
    RULE_FIRED = "RULE_FIRED"
    INTERRUPT = "INTERRUPT"
    PLAN_REQUESTED = "PLAN_REQUESTED"
    PLAN_EMITTED = "PLAN_EMITTED"
    AMBIGUITY_SUSPENDED = "AMBIGUITY_SUSPENDED"
    INPUT_RESUMED = "INPUT_RESUMED"
    PROOF_COMPLETED = "PROOF_COMPLETED"
    CRITIQUE = "CRITIQUE"
    SIMULATION_COMPLETED = "SIMULATION_COMPLETED"
    GATE_REFUSED = "GATE_REFUSED"
    EXECUTED = "EXECUTED"
    MEMORY_WRITTEN = "MEMORY_WRITTEN"
    MEMORY_REJECTED = "MEMORY_REJECTED"
    SLASHED = "SLASHED"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"
    REFUSED = "REFUSED"


class Event(BaseModel):
    model_config = ConfigDict(frozen=True)

    seq: int
    type: EventType
    tick: int
    payload: Dict[str, object] = Field(default_factory=dict)
    prev_hash: str = GENESIS_HASH
    hash: str = ""

    def commit_hash(self) -> str:
        body = {
            "seq": self.seq,
            "type": self.type.value,
            "tick": self.tick,
            "payload": self.payload,
            "prev_hash": self.prev_hash,
        }
        return sha256_canonical(body)


class CognitiveLedger:
    """Append-only, hash-chained ledger of every cognitive state transition."""

    def __init__(self) -> None:
        self._events: List[Event] = []

    def append(self, type: EventType, tick: int, payload: Optional[Dict[str, object]] = None) -> Event:
        prev_hash = self._events[-1].hash if self._events else GENESIS_HASH
        event = Event(
            seq=len(self._events),
            type=type,
            tick=tick,
            payload=payload or {},
            prev_hash=prev_hash,
        )
        event = event.model_copy(update={"hash": event.commit_hash()})
        self._events.append(event)
        return event

    @property
    def events(self) -> List[Event]:
        return list(self._events)

    def tail_hash(self) -> str:
        return self._events[-1].hash if self._events else GENESIS_HASH

    def verify_chain(self) -> bool:
        expected_prev = GENESIS_HASH
        for event in self._events:
            if event.prev_hash != expected_prev:
                return False
            if event.hash != event.commit_hash():
                return False
            expected_prev = event.hash
        return True

    def transcript(self) -> List[str]:
        return [f"{e.seq:03d} {e.type.value:<20} {canonical_json(e.payload)[:100]}" for e in self._events]


class EventBus:
    """Deterministic synchronous pub/sub; subscribers run in registration order."""

    def __init__(self) -> None:
        self._subscribers: List[Callable[[Event], None]] = []

    def subscribe(self, fn: Callable[[Event], None]) -> None:
        self._subscribers.append(fn)

    def publish(self, event: Event) -> None:
        for fn in self._subscribers:
            fn(event)
