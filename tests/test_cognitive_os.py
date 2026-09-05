"""Avaira Cognitive OS v5.0 — 21 new tests.

Pure-stdlib + pydantic, fully offline, deterministic (seeded RNG, logical
clocks). Covers the five pillars: cognitive kernel, virtual memory,
world model & formal proof, hardened execution gate, loop orchestration.
"""
from __future__ import annotations

import pytest

from avaira_os.agent_os import AgentOS
from avaira_os.events import CognitiveLedger, EventType
from avaira_os.execution_gate import (EVMFreezeSlashAdapter, InsufficientStake,
                                      LocalLedgerSlashing, RefusalReason)
from avaira_os.kernel import (ChunkKind, GlobalWorkingMemory,
                              ProductionRule, RuleEngine)
from avaira_os.memory_tiers import SelfEditingMemory, WriteDecision
from avaira_os.reasoning import AmbiguityError, System2Planner, TraceRequired
from avaira_os.schemas import (ArtifactType, Bound, Envelope, ParamBound,
                               ReasoningTrace, SafetyCertificate,
                               VerificationArtifact, Verdict)
from avaira_os.world_model import ShadowSandbox, SymbolicProver

SECRET = "test-secret-avaira-v5"


def _envelope(cap: float = 100.0) -> Envelope:
    return Envelope(
        cost_cap_usd=cap,
        allowed_actions=["build_artifact", "run_tests", "deploy_release",
                         "send_payment", "web_search"],
        hard_bounds={
            "cash_usd": Bound(lo=0.0, hi=cap),
            "spend_total_usd": Bound(lo=0.0, hi=cap),
        },
    )


def _os(stake: float = 100.0) -> AgentOS:
    return AgentOS(envelope=_envelope(), secret=SECRET,
                   stake=LocalLedgerSlashing(initial_stakes={"avaira-agent-01": stake}))


# ===========================================================================
# Pillar A1 — Global Working Memory (kernel.py)  [tests 1-3]
# ===========================================================================


class TestGlobalWorkingMemory:
    def test_capacity_is_seven_plus_minus_two_and_evicts_lowest_activation(self):
        gwm = GlobalWorkingMemory()
        assert gwm.capacity == 7
        with pytest.raises(ValueError):
            GlobalWorkingMemory(capacity=4)  # outside 7±2
        gwm.set_goal("maximize yield")
        for i in range(10):  # exceed capacity: eviction must kick in
            chunk = gwm.insert(ChunkKind.PERCEPT, f"percept {i}")
            if i < 6:
                gwm.touch(chunk.id)  # keep early chunks warm
        assert len(gwm) == 7
        assert gwm.goal is not None  # goal survived the pressure

    def test_activation_decay_reduces_activation_and_evicts_cold_chunks(self):
        gwm = GlobalWorkingMemory()
        chunk = gwm.insert(ChunkKind.PERCEPT, "cold fact", activation=0.10)
        for _ in range(50):  # 50 decay steps drive 0.10 -> ~0.008
            gwm.decay()
        assert gwm.get(chunk.id) is None  # cold chunk decayed out
        warm = gwm.insert(ChunkKind.PERCEPT, "warm fact", activation=0.9)
        gwm.decay()
        assert gwm.get(warm.id).activation < 0.9  # decayed but retained

    def test_goal_chunk_is_protected_from_eviction_and_decay(self):
        gwm = GlobalWorkingMemory(capacity=5)
        gwm.set_goal("protect me")
        for i in range(20):  # sustained insertion pressure
            gwm.insert(ChunkKind.PERCEPT, f"noise {i}")
        assert gwm.goal is not None and gwm.goal.content == "protect me"
        for _ in range(100):  # decay would kill any unpinned chunk
            gwm.decay()
        assert gwm.goal is not None and gwm.goal.content == "protect me"


# ===========================================================================
# Pillar A1 — Production rules & interrupts (kernel.py)  [tests 4-5]
# ===========================================================================


class TestProductionRules:
    def test_rules_fire_in_priority_order(self):
        gwm = GlobalWorkingMemory()
        gwm.set_goal("demo")
        engine = RuleEngine()
        fired = []
        engine.register(ProductionRule(
            name="low", priority=2, condition=lambda m: m.goal is not None,
            action=lambda m: fired.append("low")))
        engine.register(ProductionRule(
            name="high", priority=8, condition=lambda m: m.goal is not None,
            action=lambda m: fired.append("high")))
        fired_names = engine.evaluate(gwm)
        assert fired_names[0] == "high" and "low" in fired_names
        assert fired == ["high", "low"]

    def test_priority_nine_rule_interrupts_loop_before_execution(self):
        os = _os()
        os.register_rule(ProductionRule(
            name="halt_all", priority=10,
            condition=lambda m: m.goal is not None,
            message="halted by operator reflex"))
        result = os.run("deploy the payments service release")
        assert result.status.value == "ABORTED"
        assert "halt_all" in result.interrupt
        # the interrupt aborted the loop BEFORE any side effect
        assert all(e.type != EventType.EXECUTED for e in os.ledger.events)
        assert os.audit is None
        assert any(e.type == EventType.INTERRUPT for e in os.ledger.events)


# ===========================================================================
# Pillar A2 — System-2 reasoning (reasoning.py)  [tests 6-8]
# ===========================================================================


class TestSystem2Reasoning:
    def test_plan_requires_complete_reasoning_trace(self):
        planner = System2Planner()
        plan = planner.plan("pay vendor invoice of $30", GlobalWorkingMemory(), _envelope())
        assert plan.trace.is_complete()
        assert plan.trace.decomposition and plan.trace.risk_analysis
        assert plan.trace.alternatives and plan.trace.decision

    def test_incomplete_trace_is_refused_fail_closed(self):
        plan = _os().planner.plan("pay vendor invoice of $30", GlobalWorkingMemory(), _envelope())
        tampered = plan.model_copy(update={
            "trace": ReasoningTrace(decomposition=["only one section filled"]),
        })
        with pytest.raises(TraceRequired):
            System2Planner()._finalize(tampered)

    def test_ambiguous_goal_raises_for_human_answer(self):
        planner = System2Planner()
        with pytest.raises(AmbiguityError) as excinfo:
            planner.plan("pay the vendor invoice", GlobalWorkingMemory(), _envelope())
        assert excinfo.value.missing_param == "amount_usd"
        assert excinfo.value.question  # a real question for the operator


# ===========================================================================
# Pillar B — Three-tier memory & proof-gated self-editing  [tests 9-11]
# ===========================================================================


class TestMemoryTiers:
    def test_l2_tfidf_retrieval_ranks_relevant_episode_first(self):
        memory = SelfEditingMemory()
        memory.remember_episode("the deploy pipeline passed all tests today")
        memory.remember_episode("vendor invoice for hardware arrived late")
        memory.remember_episode("deploy rollback executed after alert")
        hits = memory.recall("deploy pipeline tests", k=2)
        assert len(hits) == 2
        assert "deploy pipeline" in hits[0][0].text
        assert hits[0][1] > hits[1][1]

    def test_l3_writes_are_proof_gated(self):
        memory = SelfEditingMemory()
        # no artifact -> rejected, fail-closed
        rejected = memory.write_belief(
            "vendor", "reliability", "high", 0.9,
            artifact=VerificationArtifact(type=ArtifactType.HUMAN_HASH, ref="", source="operator"))
        assert rejected.decision == WriteDecision.REJECTED
        assert "no verification artifact" in rejected.reason
        assert memory.graph.get("vendor", "reliability") is None
        # valid ExecutionAudit artifact -> accepted with provenance
        accepted = memory.write_belief(
            "vendor", "reliability", "high", 0.9,
            artifact=VerificationArtifact(type=ArtifactType.EXECUTION_AUDIT,
                                          ref="AUD-9A7FC0BE37BA", source="cognitive-os-executor"))
        assert accepted.decision == WriteDecision.ACCEPTED
        assert memory.graph.get("vendor", "reliability").artifacts[0].ref == "AUD-9A7FC0BE37BA"

    def test_corroboration_rule_governs_belief_reversal(self):
        memory = SelfEditingMemory()
        memory.write_belief("vendor", "reliability", "high", 0.9,
                            artifact=VerificationArtifact(type=ArtifactType.EXECUTION_AUDIT,
                                                          ref="AUD-1", source="executor"))
        # reversal with LOWER confidence and one artifact -> rejected
        weak = memory.write_belief("vendor", "reliability", "low", 0.4,
                                   artifact=VerificationArtifact(type=ArtifactType.HUMAN_HASH,
                                                                 ref="H-1", source="operator"))
        assert weak.decision == WriteDecision.REJECTED
        assert "strictly higher confidence" in weak.reason
        # reversal with strictly higher confidence -> accepted
        strong = memory.write_belief("vendor", "reliability", "low", 0.95,
                                     artifact=VerificationArtifact(type=ArtifactType.HUMAN_HASH,
                                                                   ref="H-2", source="operator"))
        assert strong.decision == WriteDecision.ACCEPTED and strong.belief.revision == 2
        # reversal at lower confidence BUT two independent artifacts -> accepted
        memory.write_belief("vendor", "uptime", "flaky", 0.9,
                            artifact=VerificationArtifact(type=ArtifactType.SAFETY_CERTIFICATE,
                                                          ref="C-1", source="prover"))
        corroborated = memory.write_belief("vendor", "uptime", "stable", 0.5,
                                           artifact=VerificationArtifact(type=ArtifactType.HUMAN_HASH,
                                                                         ref="H-3", source="operator"),
                                           corroborating=VerificationArtifact(type=ArtifactType.SAFETY_CERTIFICATE,
                                                                              ref="C-2", source="auditor"))
        assert corroborated.decision == WriteDecision.ACCEPTED
        # two artifacts from the SAME source are not independent -> rejected
        memory.write_belief("vendor", "latency", "fast", 0.9,
                            artifact=VerificationArtifact(type=ArtifactType.SAFETY_CERTIFICATE,
                                                          ref="C-3", source="prover"))
        same_source = memory.write_belief("vendor", "latency", "slow", 0.5,
                                          artifact=VerificationArtifact(type=ArtifactType.HUMAN_HASH,
                                                                        ref="H-4", source="operator"),
                                          corroborating=VerificationArtifact(type=ArtifactType.SAFETY_CERTIFICATE,
                                                                             ref="C-4", source="operator"))
        assert same_source.decision == WriteDecision.REJECTED
        assert "not independent" in same_source.reason


# ===========================================================================
# Pillar C — Proof-of-Safety & shadow sandbox (world_model.py)  [tests 12-16]
# ===========================================================================


class TestWorldModel:
    def _pay_plan(self, lo: float, hi: float):
        return System2Planner().plan(
            "pay vendor invoice", GlobalWorkingMemory(), _envelope(),
            context={"amount_usd": ParamBound(name="amount_usd", lo=lo, hi=hi)})

    def test_prover_returns_safe_for_bounded_plan(self):
        proof = SymbolicProver().prove(self._pay_plan(20, 30), _envelope(), {"cash_usd": 100.0})
        assert proof.verdict == Verdict.SAFE
        assert proof.final_state["cash_usd"] == (70.0, 80.0)
        assert proof.witness is None

    def test_prover_returns_unsafe_with_witness_counterexample(self):
        proof = SymbolicProver().prove(self._pay_plan(80, 120), _envelope(), {"cash_usd": 100.0})
        assert proof.verdict == Verdict.UNSAFE
        witness = proof.witness
        assert witness is not None
        assert witness.breach == "below_lo" and witness.variable == "cash_usd"
        assert witness.observed_interval[0] < 0.0
        assert witness.params["amount_usd"] == 120.0  # concrete counterexample spend

    def test_prover_returns_unknown_fail_closed_for_unprovable_plan(self):
        plan = self._pay_plan(10, 20)
        step = plan.steps[0].model_copy(update={"action": "drain_treasury"})
        plan = plan.model_copy(update={"steps": [step]})
        proof = SymbolicProver().prove(plan, _envelope(), {"cash_usd": 100.0})
        assert proof.verdict == Verdict.UNKNOWN
        assert "whitelist" in proof.reason

    def test_over_budget_plan_is_clamped_to_95_dollars(self):
        result = _os().run("pay vendor invoice of $120")
        assert result.status.value == "COMPLETED"
        assert result.verdict == Verdict.SAFE.value
        assert result.audit.final_state["spend_total_usd"] == 95.0
        assert result.audit.final_state["cash_usd"] == 5.0
        assert any("UNSAFE" in line for line in result.transcript)  # the catch is on the ledger

    def test_shadow_sandbox_is_deterministic_and_reports_confidence(self):
        plan = self._pay_plan(20, 30)
        envelope = _envelope()
        first = ShadowSandbox(runs=200, seed=0x5EED).simulate(plan, envelope, {"cash_usd": 100.0})
        second = ShadowSandbox(runs=200, seed=0x5EED).simulate(plan, envelope, {"cash_usd": 100.0})
        assert first.runs == 200 and first.violations == 0 and first.confidence == 1.0
        assert first == second  # identical seed -> identical result
        bad = ShadowSandbox(runs=200, seed=0x5EED).simulate(
            self._pay_plan(80, 120), envelope, {"cash_usd": 100.0})
        # samples above the $100 balance violate the hard rule, samples below
        # it do not: the sandbox reports partial confidence, the prover the
        # worst case
        assert 0 < bad.violations < 200 and bad.confidence < 1.0


# ===========================================================================
# Pillar D — Execution gate, slashing, EVM settlement  [tests 17-20]
# ===========================================================================


class TestExecutionGate:
    def _plan_and_cert(self, key: str = SECRET):
        os = _os()
        plan = os.planner.plan("pay vendor invoice of $40", GlobalWorkingMemory(), _envelope())
        proof = os.prover.prove(plan, _envelope(), os.initial_state)
        assert proof.verdict == Verdict.SAFE
        certificate = SafetyCertificate(
            plan_hash=plan.plan_hash(), verdict=Verdict.SAFE, nonce="nonce-1", issued_tick=1,
        ).sign(key)
        return os, plan, certificate

    def test_gate_approves_valid_attestation_certificate_and_envelope(self):
        os, plan, certificate = self._plan_and_cert()
        attestation = os.attestations.issue("avaira-agent-01", nonce="boot-1")
        decision = os.gate.authorize(plan, certificate, attestation, _envelope())
        assert decision.allowed is True
        assert decision.refusals == []
        assert "hardware_attestation" in decision.checks_passed
        assert "certificate_signature" in decision.checks_passed
        assert "cost_under_cap" in decision.checks_passed

    def test_gate_refusal_matrix_fail_closed(self):
        os, plan, certificate = self._plan_and_cert()
        attestation = os.attestations.issue("avaira-agent-01", nonce="boot-1")
        # (a) missing attestation
        d = os.gate.authorize(plan, certificate, None, _envelope())
        assert RefusalReason.MISSING_ATTESTATION in d.refusals
        # (b) wrong PCR0 measurement
        forged_tee = attestation.model_copy(update={"pcr0": "f" * 64})
        assert RefusalReason.INVALID_ATTESTATION in os.gate.authorize(
            plan, certificate, forged_tee, _envelope()).refusals
        # (c) certificate signed by a foreign key
        attacker_os, attacker_plan, attacker_cert = self._plan_and_cert(key="attacker-key")
        assert RefusalReason.INVALID_CERTIFICATE_SIGNATURE in attacker_os.gate.authorize(
            attacker_plan, attacker_cert, attacker_os.attestations.issue("a", "n"),
            _envelope()).refusals
        # (d) valid certificate bound to a DIFFERENT plan
        other_plan = os.planner.plan("pay vendor invoice of $41", GlobalWorkingMemory(), _envelope())
        assert RefusalReason.PLAN_HASH_MISMATCH in os.gate.authorize(
            other_plan, certificate, attestation, _envelope()).refusals
        # (e) cost exactly at cap: the gate requires Cost < Cap strictly
        cap_plan = os.planner.plan("pay vendor invoice of $100", GlobalWorkingMemory(), _envelope())
        assert cap_plan.total_cost_hi() == 100.0  # prover math allows <= cap
        cap_cert = SafetyCertificate(plan_hash=cap_plan.plan_hash(), verdict=Verdict.SAFE,
                                     nonce="n", issued_tick=1).sign(SECRET)
        cap_decision = os.gate.authorize(cap_plan, cap_cert, attestation, _envelope())
        assert RefusalReason.COST_CAP_EXCEEDED in cap_decision.refusals

    def test_ledger_slashing_is_atomic_and_hash_chained(self):
        stake = LocalLedgerSlashing(initial_stakes={"agent": 100.0})
        receipt = stake.burn("agent", 25.0, "violation", evidence_hash="e" * 64)
        assert receipt.amount_burned == 25.0 and stake.stake_of("agent") == 75.0
        with pytest.raises(InsufficientStake):  # atomic: 75 < 200, nothing burns
            stake.burn("agent", 200.0, "overburn", evidence_hash="f" * 64)
        assert stake.stake_of("agent") == 75.0
        assert stake.verify_chain("agent")

    def test_evm_adapter_builds_freeze_and_slash_settlement(self):
        adapter = EVMFreezeSlashAdapter(
            contract_address="0x5eb3E0eE3bE9E0964b0F1Eaa3Cd2bE74ba3746C2")
        tx = adapter.build_settlement("0x1111111111111111111111111111111111111111",
                                      25.0, "forged safety certificate")
        assert tx["function"] == "freezeAndSlash(address,uint256,string)"
        assert tx["dry_run"] is True
        assert tx["args"]["slashAmount"] == 25 * 10**18
        data = tx["data"]
        assert data.startswith("0x") and len(data) >= 2 + 4 + 32 * 4  # selector + head + len + data word
        eth_utils = pytest.importorskip("eth_utils")
        expected = "0x" + eth_utils.keccak(text="freezeAndSlash(address,uint256,string)")[:4].hex()
        assert adapter.selector == expected


# ===========================================================================
# Pillar E — DCG loop, critique back-edges, ledger (agent_os.py)  [test 21]
# ===========================================================================


class TestAgentOSLoop:
    def test_dcg_loop_contract(self):
        # -- full cycle PLAN -> PROVE -> SIMULATE -> EXECUTE
        os = _os()
        result = os.run("deploy the payments service release")
        types = [e.type for e in os.ledger.events]
        for expected in (EventType.GOAL_SET, EventType.PLAN_EMITTED, EventType.PROOF_COMPLETED,
                         EventType.SIMULATION_COMPLETED, EventType.EXECUTED, EventType.COMPLETED):
            assert expected in types, f"missing {expected} in the DCG loop"
        assert result.verdict == Verdict.SAFE.value
        # -- self-correction: first draft was under-budgeted, prover caught it,
        #    a CRITIQUE back-edge re-routed to PLAN, and the repaired plan ran
        critiques = [e for e in os.ledger.events if e.type == EventType.CRITIQUE]
        assert critiques and critiques[0].payload["origin"] == "prover"
        assert critiques[0].payload["back_edge"] == "PLAN"
        assert result.iterations == 1  # repaired plan is the second draft
        # -- ambiguity: underspecified goal suspends at AWAIT_INPUT, answer resumes
        os2 = _os()
        suspended = os2.run("pay the vendor invoice")
        assert suspended.status.value == "AWAIT_INPUT"
        assert suspended.pending_question_id == "amount_usd"
        resumed = os2.submit_answer("amount_usd", 20.0, 30.0)
        assert resumed.status.value == "COMPLETED"
        resumed_types = [e.type for e in os2.ledger.events]
        assert EventType.AMBIGUITY_SUSPENDED in resumed_types
        assert EventType.INPUT_RESUMED in resumed_types
        # -- slash: a forced violation is refused by the gate BEFORE execution,
        #    and the stake burns atomically
        os3 = _os(stake=100.0)
        slashed = os3.run_forced_violation("pay vendor invoice of $40")
        assert slashed.status.value == "SLASHED"
        assert RefusalReason.INVALID_CERTIFICATE_SIGNATURE.value in slashed.gate_refusals
        assert os3.audit is None
        assert slashed.slash_receipt.amount_burned == 25.0
        assert os3.stake.stake_of("avaira-agent-01") == 75.0
        # -- the cognitive ledger is tamper-evident
        assert os3.ledger.verify_chain()
        ledger = CognitiveLedger()
        ledger.append(EventType.GOAL_SET, 1, {"goal": "demo"})
        ledger.append(EventType.PLAN_EMITTED, 2, {"plan_hash": "abc"})
        assert ledger.verify_chain()
        ledger._events[1] = ledger.events[1].model_copy(update={"payload": {"plan_hash": "evil"}})
        assert ledger.verify_chain() is False
