"""Avaira Cognitive OS v5.0 — Pillar A: System-2 reasoning.

The planner is deterministic and offline (no LLM, no network). Its hard
constraint is structural: it may not emit a `Plan` unless it has produced a
complete `ReasoningTrace` — Decomposition → Risk Analysis → Alternatives →
Decision. An incomplete trace raises `TraceRequired` (fail-closed).

When a proof or simulation rejects a plan, the `Critique` (with its witness
counterexample) is fed back in and the planner repairs the offending
parameter — clamping spend to what the envelope mathematically allows, with
a 5% safety margin. Underspecified goals raise `AmbiguityError`, which the
OS turns into an AWAIT_INPUT suspension.
"""
from __future__ import annotations

import math
import re
from typing import Dict, List, Optional

from .kernel import ChunkKind, GlobalWorkingMemory
from .schemas import (Critique, Effect, EffectKind, Envelope, ParamBound,
                      Plan, PlanStep, ReasoningTrace, Witness)

SAFETY_MARGIN = 0.95  # clamped spends keep a 5% margin under the mathematical limit


class TraceRequired(Exception):
    """Fail-closed: no plan may be emitted without a complete reasoning trace."""


class AmbiguityError(Exception):
    """The goal is underspecified — the OS must suspend at AWAIT_INPUT."""

    def __init__(self, question_id: str, question: str, missing_param: str) -> None:
        super().__init__(f"ambiguous goal: {question}")
        self.question_id = question_id
        self.question = question
        self.missing_param = missing_param


class PlanningRefused(Exception):
    """No admissible plan exists under the envelope — fail closed."""


# ---------------------------------------------------------------------------
# Deterministic goal templates
# ---------------------------------------------------------------------------

_GOAL_AMOUNT_RE = re.compile(r"\$?\s*(\d+(?:\.\d+)?)")


def _finite(lo: float, hi: float) -> ParamBound:
    return ParamBound(name="", lo=float(lo), hi=float(hi))


def _spend(step_id: str, action: str, variable: str, param: str, lo: float, hi: float,
           description: str = "") -> PlanStep:
    return PlanStep(
        id=step_id,
        action=action,
        params={param: ParamBound(name=param, lo=lo, hi=hi)},
        effects=[Effect(kind=EffectKind.SPEND, variable=variable, amount_param=param)],
        description=description,
    )


def _trace(decomposition: List[str], risks: List[str], alternatives: List[str],
           decision: str) -> ReasoningTrace:
    return ReasoningTrace(
        decomposition=decomposition,
        risk_analysis=risks,
        alternatives=alternatives,
        decision=decision,
    )


def _plan_deploy(goal: str, envelope: Envelope, context: Dict[str, ParamBound],
                 critique: Optional[Critique]) -> List[PlanStep]:
    cash = envelope.bound_of("cash_usd")
    budget = cash.hi if cash else envelope.cost_cap_usd
    if critique is None:
        # First draft: optimistically bounded release. The prover/sandbox is
        # expected to catch the under-budgeted deploy step.
        return [
            _spend("build", "build_artifact", "cash_usd", "cost_usd",
                   min(50.0, budget * 0.5), min(55.0, budget * 0.55), "compile release artifact"),
            _spend("test", "run_tests", "cash_usd", "cost_usd", 5.0, 8.0, "verification suite"),
            _spend("deploy", "deploy_release", "cash_usd", "cost_usd", 40.0, 60.0, "publish release"),
        ]
    return [
        _spend("build", "build_artifact", "cash_usd", "cost_usd",
               min(50.0, budget * 0.5), min(55.0, budget * 0.55), "compile release artifact"),
        _spend("test", "run_tests", "cash_usd", "cost_usd", 5.0, 8.0, "verification suite"),
        _spend("deploy", "deploy_release", "cash_usd", "cost_usd", 30.0, 40.0, "publish release"),
    ]


def _plan_pay(goal: str, envelope: Envelope, context: Dict[str, ParamBound],
              critique: Optional[Critique]) -> List[PlanStep]:
    bound = context.get("amount_usd")
    if bound is None:
        match = _GOAL_AMOUNT_RE.search(goal)
        if match:
            value = float(match.group(1))
            bound = ParamBound(name="amount_usd", lo=value, hi=value)
    if bound is None:
        raise AmbiguityError(
            question_id="amount_usd",
            question="What is the exact payment amount in USD?",
            missing_param="amount_usd",
        )
    return [
        _spend("pay", "send_payment", "cash_usd", "amount_usd",
               bound.lo, bound.hi, "settle vendor invoice"),
    ]


def _plan_research(goal: str, envelope: Envelope, context: Dict[str, ParamBound],
                   critique: Optional[Critique]) -> List[PlanStep]:
    return [
        _spend("search", "web_search", "cash_usd", "cost_usd", 0.0, min(1.0, envelope.cost_cap_usd * 0.01),
               "gather sources"),
    ]


_TEMPLATES: List[tuple] = [
    ({"deploy", "release", "ship"}, _plan_deploy),
    ({"pay", "invoice", "purchase", "buy"}, _plan_pay),
    ({"research", "investigate", "analyze"}, _plan_research),
]


def _select_template(goal: str):
    lowered = goal.lower()
    for keywords, fn in _TEMPLATES:
        if any(k in lowered for k in keywords):
            return fn
    return _plan_research


# ---------------------------------------------------------------------------
# Critique repair
# ---------------------------------------------------------------------------


def _clamp_witnessed_spend(plan: Plan, witness: Witness, envelope: Envelope,
                           initial_state: Dict[str, float]) -> Optional[PlanStep]:
    """Recompute the offending spend parameter from the envelope's hard math."""
    idx = next((i for i, s in enumerate(plan.steps) if s.id == witness.step_id), None)
    if idx is None:
        return None
    step = plan.steps[idx]
    spend_effects = [e for e in step.effects if e.kind == EffectKind.SPEND]
    if not spend_effects:
        return None
    effect = spend_effects[0]
    param = step.params.get(effect.amount_param)
    if param is None:
        return None

    limit = float("inf")
    spent_hi_before = 0.0
    spent_lo_before = 0.0
    for prior in plan.steps[:idx]:
        for e in prior.effects:
            if e.kind == EffectKind.SPEND and e.variable == effect.variable:
                spent_hi_before += prior.params[e.amount_param].hi
                spent_lo_before += prior.params[e.amount_param].lo

    if witness.breach == "below_lo":
        hard_lo = envelope.bound_of(effect.variable)
        lo_limit = hard_lo.lo if hard_lo else 0.0
        floor_before = initial_state.get(effect.variable, 0.0) - spent_hi_before
        limit = floor_before - lo_limit
    elif witness.breach == "above_hi":
        hard = envelope.bound_of(effect.variable)
        hi_limit = hard.hi if hard else envelope.cost_cap_usd
        ceiling_before = spent_lo_before
        limit = hi_limit - ceiling_before
    if not math.isfinite(limit):
        return None

    new_hi = math.floor(min(param.hi, limit) * SAFETY_MARGIN * 100) / 100.0
    new_lo = min(param.lo, new_hi)
    if new_hi < 0:
        return None
    repaired = step.model_copy(deep=True)
    repaired.params[effect.amount_param] = ParamBound(name=param.name, lo=new_lo, hi=new_hi)
    return repaired


def _repaired_plan(plan: Plan, critique: Critique, envelope: Envelope,
                   initial_state: Dict[str, float]) -> Plan:
    if critique.witness is None:
        return plan
    repaired_step = _clamp_witnessed_spend(plan, critique.witness, envelope, initial_state)
    if repaired_step is None:
        return plan
    steps = [repaired_step if s.id == repaired_step.id else s for s in plan.steps]
    return plan.model_copy(update={"steps": steps})


# ---------------------------------------------------------------------------
# The planner
# ---------------------------------------------------------------------------


class System2Planner:
    """Deterministic System-2 planner with a mandatory reasoning trace."""

    def __init__(self) -> None:
        self.last_trace: Optional[ReasoningTrace] = None

    def plan(self, goal: str, gwm: GlobalWorkingMemory, envelope: Envelope,
             critique: Optional[Critique] = None, context: Optional[Dict[str, ParamBound]] = None,
             initial_state: Optional[Dict[str, float]] = None) -> Plan:
        context = dict(context or {})
        # answers previously supplied at AWAIT_INPUT live in working memory
        for chunk in gwm.by_kind(ChunkKind.ANSWER):
            if ":" in chunk.content:
                name, raw = chunk.content.split(":", 1)
                try:
                    lo, hi = (float(part) for part in raw.split(".."))
                    context.setdefault(name.strip(), ParamBound(name=name.strip(), lo=lo, hi=hi))
                except ValueError:
                    continue

        template = _select_template(goal)
        try:
            steps = template(goal, envelope, context, critique)
        except AmbiguityError:
            raise
        steps = [s for s in steps if s.action in envelope.allowed_actions]
        if not steps:
            raise PlanningRefused("template produced no steps admissible under the envelope")

        if critique is not None and critique.witness is not None:
            steps = _repaired_plan(
                Plan(goal=goal, steps=steps, trace=ReasoningTrace(), iteration=critique.iteration),
                critique, envelope, initial_state or {},
            ).steps

        iteration = critique.iteration + 1 if critique else 0
        plan = Plan(
            goal=goal,
            steps=steps,
            trace=self._build_trace(goal, steps, envelope, critique),
            critique=critique,
            iteration=iteration,
        )
        return self._finalize(plan)

    # -- internals -------------------------------------------------------------

    def _build_trace(self, goal: str, steps: List[PlanStep], envelope: Envelope,
                     critique: Optional[Critique]) -> ReasoningTrace:
        decomposition = [f"{s.id}: {s.action} ({s.description or 'step'})" for s in steps]
        risks = [f"worst-case spend ${plan_cost(steps):.2f} vs cap ${envelope.cost_cap_usd:.2f}"]
        if critique is not None:
            risks.append(f"repairing {critique.origin} critique: {critique.reason}")
            if critique.witness is not None:
                risks.append(
                    f"witness: step '{critique.witness.step_id}' drives "
                    f"'{critique.witness.variable}' {critique.witness.breach}"
                )
        alternatives = ["clamp spend parameters within envelope math", "defer task to human operator"]
        decision = "emit repaired plan" if critique else "emit first-draft plan"
        return _trace(decomposition, risks, alternatives, decision)

    def _finalize(self, plan: Plan) -> Plan:
        if not plan.trace.is_complete():
            raise TraceRequired("refusing to emit a plan without a complete reasoning trace")
        self.last_trace = plan.trace
        return plan


def plan_cost(steps: List[PlanStep]) -> float:
    return round(sum(
        step.params[e.amount_param].hi
        for step in steps for e in step.effects if e.kind == EffectKind.SPEND
    ), 10)
