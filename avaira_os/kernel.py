"""Avaira Cognitive OS v5.0 — Pillar A: the Cognitive Kernel.

`GlobalWorkingMemory` is a slot-based memory of 7±2 chunks with activation
decay. The Goal Chunk is pinned: decay applies, eviction never.

`RuleEngine` is a priority-based reflex system. A matching rule with
priority >= 9 raises `InterruptSignal`, aborting whatever loop is running —
reflexes outrank deliberation.
"""
from __future__ import annotations

import math
from enum import Enum
from typing import Callable, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ChunkKind(str, Enum):
    GOAL = "GOAL"
    PERCEPT = "PERCEPT"
    PLAN = "PLAN"
    CRITIQUE = "CRITIQUE"
    ANSWER = "ANSWER"
    EPISODE = "EPISODE"


class Chunk(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    kind: ChunkKind
    content: str
    activation: float = 0.5
    created_tick: int = 0
    last_access_tick: int = 0
    protected: bool = False


class InterruptSignal(Exception):
    """Raised by a priority >= 9 production rule to abort the current loop."""

    def __init__(self, rule_name: str, priority: int, reason: str = "") -> None:
        super().__init__(f"interrupt: rule {rule_name!r} (priority {priority}): {reason}")
        self.rule_name = rule_name
        self.priority = priority
        self.reason = reason


class GlobalWorkingMemory:
    """Slot-based working memory: 7±2 chunks, activation decay, protected goal.

    Time is a *logical tick* (never wall-clock) so behaviour is fully
    deterministic and replayable.
    """

    CAPACITY_MIN = 5
    CAPACITY_MAX = 9
    DEFAULT_CAPACITY = 7

    DECAY_LAMBDA = 0.05          # exponential decay per tick
    ACCESS_BONUS = 0.3           # activation bump on read/write
    ACTIVATION_FLOOR = 0.0
    ACTIVATION_CEIL = 1.0

    def __init__(self, capacity: int = DEFAULT_CAPACITY, goal_chunk_id: str = "chunk-goal") -> None:
        if not (self.CAPACITY_MIN <= capacity <= self.CAPACITY_MAX):
            raise ValueError(f"working memory capacity must be 7±2 (got {capacity})")
        self.capacity = capacity
        self._slots: Dict[str, Chunk] = {}
        self.tick = 0
        self._goal_chunk_id = goal_chunk_id

    # -- goal ----------------------------------------------------------------

    def set_goal(self, content: str) -> Chunk:
        chunk = Chunk(
            id=self._goal_chunk_id,
            kind=ChunkKind.GOAL,
            content=content,
            activation=self.ACTIVATION_CEIL,
            created_tick=self.tick,
            last_access_tick=self.tick,
            protected=True,
        )
        self._slots[chunk.id] = chunk
        return chunk

    @property
    def goal(self) -> Optional[Chunk]:
        return self._slots.get(self._goal_chunk_id)

    # -- core operations ------------------------------------------------------

    def insert(self, kind: ChunkKind, content: str, chunk_id: Optional[str] = None,
               protected: bool = False, activation: float = 0.5) -> Chunk:
        self.tick += 1
        chunk = Chunk(
            id=chunk_id or f"chunk-{self.tick:04d}",
            kind=kind,
            content=content,
            activation=activation,
            created_tick=self.tick,
            last_access_tick=self.tick,
            protected=protected,
        )
        self._evict_for_insert(chunk.id)
        self._slots[chunk.id] = chunk
        return chunk

    def _evict_for_insert(self, incoming_id: str) -> None:
        while len(self._slots) >= self.capacity:
            evictable = [
                c for cid, c in self._slots.items()
                if cid != incoming_id and not c.protected
            ]
            if not evictable:
                return  # all remaining slots are protected — fail soft, keep memory
            victim = min(evictable, key=lambda c: (c.activation, c.last_access_tick, c.id))
            del self._slots[victim.id]

    def touch(self, chunk_id: str) -> Optional[Chunk]:
        chunk = self._slots.get(chunk_id)
        if chunk is None:
            return None
        bumped = min(self.ACTIVATION_CEIL, chunk.activation + self.ACCESS_BONUS)
        updated = chunk.model_copy(update={"activation": bumped, "last_access_tick": self.tick})
        self._slots[chunk_id] = updated
        return updated

    def decay(self) -> List[str]:
        """One decay step; returns ids of chunks evicted by decay (goal exempt)."""
        self.tick += 1
        evicted: List[str] = []
        for chunk in list(self._slots.values()):
            new_activation = chunk.activation * math.exp(-self.DECAY_LAMBDA)
            updated = chunk.model_copy(update={"activation": new_activation})
            if not updated.protected and new_activation < 0.05:
                del self._slots[chunk.id]
                evicted.append(chunk.id)
            else:
                self._slots[chunk.id] = updated
        return evicted

    def get(self, chunk_id: str) -> Optional[Chunk]:
        return self._slots.get(chunk_id)

    def by_kind(self, kind: ChunkKind) -> List[Chunk]:
        return sorted(
            (c for c in self._slots.values() if c.kind == kind),
            key=lambda c: (-c.activation, c.id),
        )

    def all(self) -> List[Chunk]:
        return sorted(self._slots.values(), key=lambda c: c.id)

    def __len__(self) -> int:
        return len(self._slots)


# ---------------------------------------------------------------------------
# Production rules
# ---------------------------------------------------------------------------

RULE_PRIORITY_MAX = 10
INTERRUPT_PRIORITY = 9  # rules >= this priority abort the loop


class ProductionRule(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    name: str
    priority: int = Field(ge=1, le=RULE_PRIORITY_MAX)
    condition: Callable[[GlobalWorkingMemory], bool]
    action: Optional[Callable[[GlobalWorkingMemory], None]] = None
    message: str = ""

    def matches(self, gwm: GlobalWorkingMemory) -> bool:
        try:
            return bool(self.condition(gwm))
        except Exception:
            return False  # a broken condition must never fire a rule

    def fire(self, gwm: GlobalWorkingMemory) -> None:
        if self.action is not None:
            self.action(gwm)


class RuleEngine:
    """Fire matching rules in priority order.

    A rule with priority >= INTERRUPT_PRIORITY (9) triggers `InterruptSignal`
    after firing its action, aborting the calling loop — reflex takes
    precedence over deliberation.
    """

    def __init__(self) -> None:
        self._rules: List[ProductionRule] = []
        self.fired_log: List[str] = []

    def register(self, rule: ProductionRule) -> None:
        self._rules.append(rule)
        self._rules.sort(key=lambda r: (-r.priority, r.name))

    def evaluate(self, gwm: GlobalWorkingMemory) -> List[str]:
        """Fire every matching non-interrupt rule (highest priority first)."""
        fired: List[str] = []
        for rule in self._rules:
            if not rule.matches(gwm):
                continue
            rule.fire(gwm)
            self.fired_log.append(rule.name)
            fired.append(rule.name)
        return fired

    def check_interrupts(self, gwm: GlobalWorkingMemory) -> None:
        """Raise `InterruptSignal` if any priority >= 9 rule matches."""
        for rule in self._rules:
            if rule.priority >= INTERRUPT_PRIORITY and rule.matches(gwm):
                rule.fire(gwm)
                self.fired_log.append(rule.name)
                raise InterruptSignal(rule_name=rule.name, priority=rule.priority, reason=rule.message)
