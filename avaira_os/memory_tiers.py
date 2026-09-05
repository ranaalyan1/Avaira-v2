"""Avaira Cognitive OS v5.0 — Pillar B: three-tier virtual memory.

L1  Working Set      — the kernel's GlobalWorkingMemory (7±2 slot chunks).
L2  Episodic Store   — append-only experiences with a pure-Python TF-IDF
                       semantic index and cosine retrieval.
L3  Belief Graph     — Subject–Predicate–Object triples with confidence and
                       provenance.

`SelfEditingMemory` gates every L3 write behind a verification artifact
(Safety Certificate | Human Hash | Execution Audit). Unverified writes are
REJECTED. The Corroboration Rule: reversing an existing belief requires
strictly higher confidence, or two independent artifacts.
"""
from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from enum import Enum
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field

from .kernel import ChunkKind, GlobalWorkingMemory
from .schemas import VerificationArtifact

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class WriteDecision(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


# ---------------------------------------------------------------------------
# L2 — Episodic store with TF-IDF semantic index
# ---------------------------------------------------------------------------


def tokenize(text: str) -> List[str]:
    return _TOKEN_RE.findall(text.lower())


class Episode(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    text: str
    tick: int
    meta: Dict[str, str] = Field(default_factory=dict)


class EpisodicStore:
    """L2: append-only episodes, retrievable by TF-IDF cosine similarity."""

    def __init__(self) -> None:
        self._episodes: List[Episode] = []

    def add(self, text: str, tick: int, meta: Optional[Dict[str, str]] = None) -> Episode:
        digest = hashlib.sha256(f"{tick}|{text}".encode()).hexdigest()[:12]
        episode = Episode(id=f"ep-{digest}", text=text, tick=tick, meta=meta or {})
        self._episodes.append(episode)
        return episode

    def __len__(self) -> int:
        return len(self._episodes)

    def all(self) -> List[Episode]:
        return list(self._episodes)

    def retrieve(self, query: str, k: int = 3) -> List[Tuple[Episode, float]]:
        if not self._episodes:
            return []
        return self._search(query, self._episodes)[:k]

    # -- TF-IDF ----------------------------------------------------------------

    @staticmethod
    def _idf(doc_tokens: List[List[str]]) -> Dict[str, float]:
        n_docs = len(doc_tokens)
        df: Counter = Counter()
        for tokens in doc_tokens:
            df.update(set(tokens))
        return {term: math.log((n_docs + 1) / (count + 1)) + 1.0 for term, count in df.items()}

    @staticmethod
    def _vector(tokens: List[str], idf: Dict[str, float]) -> Dict[str, float]:
        tf = Counter(tokens)
        return {term: (count / len(tokens)) * idf.get(term, 0.0) for term, count in tf.items()} if tokens else {}

    @staticmethod
    def _cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
        if not a or not b:
            return 0.0
        dot = sum(weight * b.get(term, 0.0) for term, weight in a.items())
        norm_a = math.sqrt(sum(w * w for w in a.values()))
        norm_b = math.sqrt(sum(w * w for w in b.values()))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _search(self, query: str, episodes: List[Episode]) -> List[Tuple[Episode, float]]:
        doc_tokens = [tokenize(ep.text) for ep in episodes]
        idf = self._idf(doc_tokens)
        query_vec = self._vector(tokenize(query), idf)
        scored = []
        for episode, tokens in zip(episodes, doc_tokens):
            score = self._cosine(query_vec, self._vector(tokens, idf))
            scored.append((episode, score))
        # deterministic ordering: score desc, then id
        return sorted(scored, key=lambda pair: (-pair[1], pair[0].id))


# ---------------------------------------------------------------------------
# L3 — Belief graph
# ---------------------------------------------------------------------------


class Belief(BaseModel):
    model_config = ConfigDict(frozen=True)

    subject: str
    predicate: str
    obj: str
    confidence: float = Field(ge=0.0, le=1.0)
    artifacts: List[VerificationArtifact] = Field(default_factory=list)
    revision: int = 1


class WriteResult(BaseModel):
    decision: WriteDecision
    reason: str
    belief: Optional[Belief] = None


class BeliefGraph:
    """L3: (subject, predicate) -> active belief, with full revision history."""

    def __init__(self) -> None:
        self._active: Dict[Tuple[str, str], Belief] = {}
        self._history: List[Belief] = []
        self.rejections: List[str] = []

    def get(self, subject: str, predicate: str) -> Optional[Belief]:
        return self._active.get((subject, predicate))

    def all(self) -> List[Belief]:
        return sorted(self._active.values(), key=lambda b: (b.subject, b.predicate))

    def history(self) -> List[Belief]:
        return list(self._history)

    def _activate(self, belief: Belief) -> None:
        key = (belief.subject, belief.predicate)
        self._active[key] = belief
        self._history.append(belief)


class SelfEditingMemory:
    """Proof-gated write access to the belief graph (L3).

    Write policy (fail-closed):
      1. No valid verification artifact  -> REJECTED.
      2. Same (subject, predicate, object): merge; confidence may rise, never fall.
      3. Reversal (same subject+predicate, different object): accepted only if
         incoming confidence is STRICTLY higher than the incumbent's, or two
         independent artifacts corroborate the incoming belief.
    """

    def __init__(self, gwm: Optional[GlobalWorkingMemory] = None) -> None:
        self.episodic = EpisodicStore()
        self.graph = BeliefGraph()
        self._gwm = gwm
        self.tick = 0

    # -- L1/L2 convenience -------------------------------------------------------

    def remember_episode(self, text: str, meta: Optional[Dict[str, str]] = None) -> Episode:
        episode = self.episodic.add(text, self.tick, meta)
        self.tick += 1
        if self._gwm is not None:
            self._gwm.insert(ChunkKind.EPISODE, text)
        return episode

    def recall(self, query: str, k: int = 3) -> List[Tuple[Episode, float]]:
        return self.episodic.retrieve(query, k)

    # -- L3 proof-gated writes ---------------------------------------------------

    def write_belief(self, subject: str, predicate: str, obj: str, confidence: float,
                     artifact: VerificationArtifact,
                     corroborating: Optional[VerificationArtifact] = None) -> WriteResult:
        if not artifact.is_valid():
            reason = "rejected: no verification artifact (proof-gated write)"
            self.graph.rejections.append(reason)
            return WriteResult(decision=WriteDecision.REJECTED, reason=reason)

        artifacts = [artifact] + ([corroborating] if corroborating is not None else [])
        if corroborating is not None and corroborating.source == artifact.source:
            reason = "rejected: corroboration artifacts are not independent (same source)"
            self.graph.rejections.append(reason)
            return WriteResult(decision=WriteDecision.REJECTED, reason=reason)

        incumbent = self.graph.get(subject, predicate)
        if incumbent is not None and incumbent.obj != obj:
            strictly_higher = confidence > incumbent.confidence
            two_independent = len([a for a in artifacts if a.is_valid()]) >= 2
            if not (strictly_higher or two_independent):
                reason = (
                    f"rejected: belief reversal requires strictly higher confidence "
                    f"(incoming {confidence:.2f} <= incumbent {incumbent.confidence:.2f}) "
                    f"or two independent artifacts (got {len(artifacts)})"
                )
                self.graph.rejections.append(reason)
                return WriteResult(decision=WriteDecision.REJECTED, reason=reason)
            belief = Belief(
                subject=subject, predicate=predicate, obj=obj,
                confidence=confidence, artifacts=artifacts,
                revision=incumbent.revision + 1,
            )
            self.graph._activate(belief)
            return WriteResult(decision=WriteDecision.ACCEPTED, reason="reversal accepted", belief=belief)

        if incumbent is not None and incumbent.obj == obj:
            merged = Belief(
                subject=subject, predicate=predicate, obj=obj,
                confidence=max(incumbent.confidence, confidence),
                artifacts=incumbent.artifacts + artifacts,
                revision=incumbent.revision + 1,
            )
            self.graph._activate(merged)
            return WriteResult(decision=WriteDecision.ACCEPTED, reason="corroborated existing belief", belief=merged)

        belief = Belief(
            subject=subject, predicate=predicate, obj=obj,
            confidence=confidence, artifacts=artifacts,
        )
        self.graph._activate(belief)
        return WriteResult(decision=WriteDecision.ACCEPTED, reason="new belief accepted", belief=belief)
