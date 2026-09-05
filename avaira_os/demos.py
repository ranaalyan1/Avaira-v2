"""Avaira Cognitive OS v5.0 — the four deterministic Proof Artifacts.

Each demo is fully offline, seeded, and reproducible: run it twice and the
transcripts are byte-identical. Run all four:

    python -m avaira_os.demos

  1. Self-Correction : sandbox catches a bug -> agent fixes -> deploys.
  2. Ambiguity       : loop suspends at AWAIT_INPUT -> resumes on answer.
  3. Math Safety     : prover returns UNSAFE for over-budget -> clamps to $95.
  4. Slash           : forced violation -> gate refuses -> stake burns.
"""
from __future__ import annotations

import sys
from typing import List

from avaira_os.agent_os import AgentOS
from avaira_os.execution_gate import LocalLedgerSlashing
from avaira_os.schemas import Bound, Envelope, Verdict

AGENT_STAKE = 100.0
CONTRACT = "0x5eb3E0eE3bE9E0964b0F1Eaa3Cd2bE74ba3746C2"


def _make_os() -> AgentOS:
    envelope = Envelope(
        cost_cap_usd=100.0,
        allowed_actions=["build_artifact", "run_tests", "deploy_release",
                         "send_payment", "web_search"],
        hard_bounds={
            "cash_usd": Bound(lo=0.0, hi=100.0),
            "spend_total_usd": Bound(lo=0.0, hi=100.0),
        },
    )
    stake = LocalLedgerSlashing(initial_stakes={"avaira-agent-01": AGENT_STAKE})
    return AgentOS(envelope=envelope, stake=stake)


def _banner(title: str) -> str:
    return f"\n{'=' * 72}\n  {title}\n{'=' * 72}"


def _transcript(os: AgentOS) -> List[str]:
    return os.ledger.transcript()


# ---------------------------------------------------------------------------
# Demo 1 — Self-Correction: sandbox catches a bug -> agent fixes -> deploys
# ---------------------------------------------------------------------------


def demo_self_correction() -> bool:
    print(_banner("PROOF ARTIFACT 1 — SELF-CORRECTION (sandbox catches a bug)"))
    os = _make_os()
    result = os.run("deploy the payments service release")
    print(f"status            : {result.status.value}")
    print(f"proof verdict     : {result.verdict}")
    print(f"sandbox confidence: {result.confidence:.3f}")
    print(f"plan hash         : {result.plan_hash[:24]}…")
    print(f"final state       : {result.audit.final_state if result.audit else '—'}")
    print("\nevent transcript:")
    for line in _transcript(os):
        print(f"  {line}")
    print(f"\nledger tamper-evident: {result.ledger_valid}")
    ok = (
        result.status.value == "COMPLETED"
        and result.verdict == Verdict.SAFE.value
        and result.confidence == 1.0
        and result.audit is not None
        and any("CRITIQUE" in line for line in result.transcript)
        and result.ledger_valid
    )
    print(f"self-correction demonstrated: {ok}")
    return ok


# ---------------------------------------------------------------------------
# Demo 2 — Ambiguity: loop suspends at AWAIT_INPUT -> resumes on answer
# ---------------------------------------------------------------------------


def demo_ambiguity() -> bool:
    print(_banner("PROOF ARTIFACT 2 — AMBIGUITY (suspend at AWAIT_INPUT, resume on answer)"))
    os = _make_os()
    # goal carries no amount -> the planner must refuse to guess
    suspended = os.run("pay the vendor invoice")
    print(f"status after run  : {suspended.status.value}")
    print(f"pending question  : {suspended.pending_question}")
    ok_suspend = suspended.status.value == "AWAIT_INPUT"
    print(f"suspended at AWAIT_INPUT: {ok_suspend}")

    resumed = os.submit_answer("amount_usd", 20.0, 30.0)
    print("\nanswer submitted  : amount_usd ∈ [20.00, 30.00]")
    print(f"status after resume: {resumed.status.value}")
    print(f"proof verdict     : {resumed.verdict}")
    print(f"final state       : {resumed.audit.final_state if resumed.audit else '—'}")
    print("\nevent transcript:")
    for line in resumed.transcript:
        print(f"  {line}")
    ok = ok_suspend and resumed.status.value == "COMPLETED" and resumed.ledger_valid
    print(f"\nambiguity handling demonstrated: {ok}")
    return ok


# ---------------------------------------------------------------------------
# Demo 3 — Math Safety: prover returns UNSAFE -> agent clamps to $95
# ---------------------------------------------------------------------------


def demo_math_safety() -> bool:
    print(_banner("PROOF ARTIFACT 3 — MATH SAFETY (UNSAFE for over-budget, clamp to $95)"))
    os = _make_os()
    result = os.run("pay vendor invoice of $120")
    print(f"status            : {result.status.value}")
    print(f"proof verdict     : {result.verdict}")
    print(f"plan iterations   : {result.iterations}")
    if result.audit is not None:
        spent = 100.0 - result.audit.final_state.get("cash_usd", 0.0)
        print(f"actual spend      : ${spent:.2f} (cap $100.00)")
    print("\nevent transcript:")
    for line in result.transcript:
        print(f"  {line}")
    ok = (
        result.status.value == "COMPLETED"
        and result.verdict == Verdict.SAFE.value
        and result.audit is not None
        and abs(100.0 - result.audit.final_state.get("cash_usd", 0.0) - 95.0) < 1e-9
        and any("UNSAFE" in line for line in result.transcript)
    )
    print(f"\nmath-safety clamp to $95 demonstrated: {ok}")
    return ok


# ---------------------------------------------------------------------------
# Demo 4 — Slash: forced violation -> gate refuses -> stake burns
# ---------------------------------------------------------------------------


def demo_slash() -> bool:
    print(_banner("PROOF ARTIFACT 4 — SLASH (forced violation, gate refuses, stake burns)"))
    os = _make_os()
    print(f"stake before      : ${os.stake.stake_of('avaira-agent-01'):.2f}")
    # The agent signs the certificate with a foreign key — a forged proof.
    result = os.run_forced_violation("pay vendor invoice of $40")
    print(f"status            : {result.status.value}")
    print(f"gate refusals     : {', '.join(result.gate_refusals)}")
    if result.slash_receipt is not None:
        print(f"stake burned      : ${result.slash_receipt.amount_burned:.2f}")
        print(f"stake remaining   : ${result.slash_receipt.remaining_stake:.2f}")
    from avaira_os.execution_gate import EVMFreezeSlashAdapter

    adapter = EVMFreezeSlashAdapter(contract_address=CONTRACT)
    tx = adapter.build_settlement(
        agent_address="0x1111111111111111111111111111111111111111",
        amount_usd=result.slash_receipt.amount_burned if result.slash_receipt else 0.0,
        reason="forged safety certificate",
    )
    print("\non-chain settlement (dry-run):")
    print(f"  to     : {tx['to']}")
    print(f"  func   : {tx['function']}")
    print(f"  data   : {str(tx['data'])[:42]}…")
    print("\nevent transcript:")
    for line in result.transcript:
        print(f"  {line}")
    ok = (
        result.status.value == "SLASHED"
        and bool(result.gate_refusals)
        and result.slash_receipt is not None
        and result.slash_receipt.amount_burned == 25.0
        and os.stake.stake_of("avaira-agent-01") == 75.0
        and os.stake.verify_chain("avaira-agent-01")
    )
    print(f"\natomic slash demonstrated: {ok}")
    return ok


DEMOS = [
    ("self_correction", demo_self_correction, "Self-Correction: bug caught -> fixed -> deployed"),
    ("ambiguity", demo_ambiguity, "Ambiguity: AWAIT_INPUT suspension -> resume"),
    ("math_safety", demo_math_safety, "Math Safety: UNSAFE -> clamp to $95"),
    ("slash", demo_slash, "Slash: gate refusal -> atomic stake burn"),
]


def main() -> int:
    results = {}
    for name, fn, _ in DEMOS:
        results[name] = fn()
    print(_banner("SUMMARY"))
    all_ok = True
    for name, _, description in DEMOS:
        status = "PASS" if results[name] else "FAIL"
        all_ok &= results[name]
        print(f"  [{status}] {name:<16} — {description}")
    print(f"\nall proof artifacts: {'PASS' if all_ok else 'FAIL'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
