# CHANGELOG

## [Unreleased]

## [5.0.0] — Cognitive OS: Hardened Execution Layer

### Added
- **`avaira_os/` package** — a deterministic, offline Cognitive Kernel where
  safety is mathematically proven before execution:
  - Pillar A `kernel.py` / `reasoning.py`: Global Working Memory (7±2 slots,
    activation decay, protected Goal Chunk), priority-based production rules
    (priority ≥ 9 → `InterruptSignal`), System-2 planner requiring a complete
    `ReasoningTrace` (Decomposition → Risk Analysis → Alternatives → Decision).
  - Pillar B `memory_tiers.py`: three-tier hierarchy — L1 working set, L2
    episodic store with TF-IDF retrieval, L3 belief graph. `SelfEditingMemory`
    rejects L3 writes without a verification artifact; belief reversals
    require strictly higher confidence or two independent artifacts.
  - Pillar C `world_model.py`: interval-arithmetic `SymbolicProver` with
    strict `SAFE` / `UNSAFE` (witness counterexample) / `UNKNOWN`
    (fail-closed) verdicts, plus a seeded 200× Monte-Carlo `ShadowSandbox`.
  - Pillar D `execution_gate.py`: strict boolean `ExecutionGate` (hardware
    attestation + signature-valid SAFE certificate + envelope compliance),
    atomic `LocalLedgerSlashing`, and `EVMFreezeSlashAdapter` rendering
    `freezeAndSlash(address,uint256,string)` settlements.
  - Pillar E `agent_os.py` / `events.py`: the PLAN → PROVE → SIMULATE →
    EXECUTE DCG loop with critique back-edges, `AWAIT_INPUT` suspension, and
    a tamper-evident hash-chained Cognitive Ledger.
- **Four deterministic Proof Artifacts** (`python -m avaira_os.demos`):
  self-correction, ambiguity suspension/resume, math-safety clamp to $95,
  and forced-violation slash with atomic stake burn.
- **21 new tests** (`tests/test_cognitive_os.py`) covering all five pillars.
- `docs/cognitive-os-v5.md` — architecture and verification-chain reference.
