# Avaira Cognitive OS v5.0 — Hardened Execution Layer for AI Agents

> Safety is mathematically proven before execution. No action is taken based
> on LLM "confidence": every action carries a signed safety certificate,
> every state transition is hash-chained, and every violation burns stake
> atomically.

The Cognitive OS lives in the [`avaira_os/`](../avaira_os/) package: pure
stdlib + Pydantic, deterministic, offline (no API keys, no network, no wall
clock — logical ticks and seeded RNG only).

## Architecture

```
                            ┌──────────────────────────────────────┐
                            │            AgentOS (agent_os.py)     │
                            │        DCG loop orchestration        │
                            └──────────────────────────────────────┘
      PLAN ──────────▶ PROVE ──────────▶ SIMULATE ──────────▶ EXECUTE
        ▲               │                  │                   │
        │  Critique     │ UNSAFE /         │ low confidence    │ Gate approves
        └───────────────┴──────────────────┘                   ▼
            back-edges                                     COMPLETED
                                                    (or SLASHED / ABORTED /
                                                     AWAIT_INPUT / REFUSED)
```

| Pillar | Modules | What it guarantees |
|---|---|---|
| **A — Cognitive Kernel** | `kernel.py`, `reasoning.py` | Slot-based Global Working Memory (7±2 chunks, activation decay, eviction-proof Goal Chunk); priority-based production rules where priority ≥ 9 raises `InterruptSignal` and aborts the loop; System-2 planner that refuses to emit a plan without a complete `ReasoningTrace` (Decomposition → Risk Analysis → Alternatives → Decision) |
| **B — Virtual Memory** | `memory_tiers.py` | L1 working set (GWM) / L2 episodic store (pure-Python TF-IDF + cosine retrieval) / L3 belief graph (S-P-O triples). `SelfEditingMemory` **rejects** L3 writes without a verification artifact (Safety Certificate, Human Hash, or Execution Audit). Corroboration Rule: belief reversals require strictly higher confidence or two *independent* artifacts |
| **C — World Model & Proof** | `world_model.py` | `SymbolicProver` walks the plan with interval arithmetic and proves every state variable stays inside hard-rule boundaries. Verdict is strictly `SAFE`, `UNSAFE` (with a concrete witness counterexample), or `UNKNOWN` (fail-closed). `ShadowSandbox` rolls the plan forward 200× with uniform sampling of the parameter bounds (seeded) to produce a confidence score |
| **D — Hardened Execution** | `execution_gate.py` | `ExecutionGate` is a strict boolean gate: valid hardware attestation (simulated Nitro enclave, PCR0 measurement) **AND** signature-valid SAFE certificate bound to the exact plan hash **AND** envelope compliance (worst-case Cost < Cap, actions whitelisted). Anything missing or ambiguous → refusal. `LocalLedgerSlashing` performs atomic (all-or-nothing, hash-chained) stake burns; `EVMFreezeSlashAdapter` renders the punishment as a `freezeAndSlash(address,uint256,string)` settlement matching `contracts/contracts/FreezeSlash.sol` |
| **E — Loop Orchestration** | `agent_os.py`, `events.py` | The DCG loop with critique back-edges; `AWAIT_INPUT` suspension/resume; the **Cognitive Ledger** — every state transition hashed into a tamper-evident chain (`sha256(seq, type, tick, payload, prev_hash)`) |

## The verification chain

```
goal ─▶ ReasoningTrace ─▶ Plan ─▶ interval proof ─▶ 200× Monte-Carlo
          (mandatory)          │              │                │
                               │        UNSAFE+witness   confidence < 1
                               │              └────┬───────────┘
                               │                   ▼ Critique back-edge
                               │                re-PLAN
                               ▼
                    SafetyCertificate (HMAC-SHA256, plan-hash-bound)
                               ▼
       TEE attestation (PCR0) ─▶ ExecutionGate ─▶ deterministic executor
                               ▼                (refusal ⇒ atomic stake burn)
                    ExecutionAudit ─▶ proof-gated L3 memory write
```

Fail-closed invariants:

1. An unprovable plan (`UNKNOWN`) is refused, never guessed.
2. An incomplete reasoning trace cannot become a plan.
3. A plan whose worst-case cost is not strictly under the cap cannot pass the gate — even if the prover's `≤` math would allow it.
4. A gate refusal of a proven-safe plan is treated as tampering: 25% of the agent's stake burns atomically and an on-chain settlement payload is rendered.
5. Every event is hash-chained; `CognitiveLedger.verify_chain()` detects any historical mutation.

## Proof Artifacts (deterministic demos)

```bash
python -m avaira_os.demos
```

| # | Artifact | What it demonstrates |
|---|---|---|
| 1 | **Self-Correction** | The first-draft deploy plan is under-budgeted; the prover returns UNSAFE with a witness; a critique back-edge re-plans with the spend clamped to what the envelope mathematically allows; the repaired plan proves SAFE, runs the 200× sandbox at confidence 1.0, and deploys |
| 2 | **Ambiguity** | "pay the vendor invoice" carries no amount — the planner refuses to guess and the loop suspends at `AWAIT_INPUT`; `submit_answer("amount_usd", 20, 30)` resumes it to completion |
| 3 | **Math Safety** | A $120 payment against a $100 cap: prover returns UNSAFE with a witness; the agent clamps to **$95** (the envelope limit with a 5% margin) and proves the repaired plan SAFE |
| 4 | **Slash** | A certificate signed with a foreign key is refused by the gate (`invalid_certificate_signature`) *before* execution; $25 of the $100 stake burns atomically and a `freezeAndSlash` EVM settlement is rendered |

Run twice — the transcripts are byte-identical.

## Tests

```bash
pytest tests/test_cognitive_os.py -q     # 21 new tests (offline, deterministic)
pytest tests/ -q                         # full suite
```

The 21 new tests map to the pillars: working memory (3), production rules &
interrupts (2), System-2 reasoning (3), three-tier memory & corroboration (3),
proof-of-safety & sandbox (5), gate/slashing/EVM (4), and the DCG loop
contract (1).
