"""Avaira Cognitive OS v5.0 — Pillar C: world model & formal proof.

`SymbolicProver` walks the plan with interval arithmetic and proves that
every tracked state variable stays inside the envelope's hard-rule
boundaries. Its verdict is strictly one of:

  SAFE    — proven, for every admissible parameter value in the declared bounds.
  UNSAFE  — proven violable; a concrete `Witness` counterexample is attached.
  UNKNOWN — the plan is outside the provable effect algebra (fail-closed).

`ShadowSandbox` complements the proof empirically: it rolls the plan forward
200×, sampling parameters uniformly from their declared bounds (seeded, so
fully deterministic), and reports a confidence score.
"""
from __future__ import annotations

import random
from typing import Dict, Optional, Tuple

from .schemas import (Bound, Effect, EffectKind, Envelope, Plan, ParamBound,
                      ProofResult, SandboxResult, Verdict, Witness)

EPS = 1e-9
DEFAULT_SANDBOX_RUNS = 200
DEFAULT_SANDBOX_SEED = 0x5EED


# ---------------------------------------------------------------------------
# Interval arithmetic
# ---------------------------------------------------------------------------


class Interval:
    """Closed real interval [lo, hi]. Immutable; ops return new instances."""

    __slots__ = ("lo", "hi")

    def __init__(self, lo: float, hi: float) -> None:
        self.lo = float(lo)
        self.hi = float(hi)

    def __repr__(self) -> str:
        return f"[{self.lo:.4f}, {self.hi:.4f}]"

    def as_tuple(self) -> Tuple[float, float]:
        return (self.lo, self.hi)

    def add(self, other: "Interval") -> "Interval":
        return Interval(self.lo + other.lo, self.hi + other.hi)

    def sub(self, other: "Interval") -> "Interval":
        return Interval(self.lo - other.hi, self.hi - other.lo)

    def contains(self, value: float) -> bool:
        return self.lo - EPS <= value <= self.hi + EPS

    def violates(self, bound: Bound) -> Optional[str]:
        """Return 'above_hi' / 'below_lo' if any reachable value exits the bound."""
        if self.hi > bound.hi + EPS:
            return "above_hi"
        if self.lo < bound.lo - EPS:
            return "below_lo"
        return None


def _interval_of(param: ParamBound) -> Interval:
    return Interval(param.lo, param.hi)


# ---------------------------------------------------------------------------
# Symbolic prover
# ---------------------------------------------------------------------------


class SymbolicProver:
    """Proof-of-Safety engine: interval-arithmetic execution of the plan."""

    def __init__(self) -> None:
        self.last_violation: Optional[Tuple[str, str]] = None

    def prove(self, plan: Plan, envelope: Envelope,
              initial_state: Dict[str, float]) -> ProofResult:
        state: Dict[str, Interval] = {}
        for var, bound in envelope.hard_bounds.items():
            value = float(initial_state.get(var, 0.0))
            if not bound.contains(value):
                return self._unknown(f"initial state '{var}'={value} already outside hard bounds")
            state[var] = Interval(value, value)

        for step in plan.steps:
            if step.action not in envelope.allowed_actions:
                return self._unknown(f"step '{step.id}' action '{step.action}' is not in the "
                                     f"envelope whitelist; its effects cannot be proven")
            for effect in step.effects:
                outcome = self._apply_effect(step, effect, state, envelope)
                if outcome is not None:
                    return outcome
            breach = self._check_bounds(state, envelope)
            if breach is not None:
                witness = self._build_witness(plan, step.id, breach, state, envelope)
                return ProofResult(
                    verdict=Verdict.UNSAFE,
                    reason=(f"step '{step.id}' drives '{breach[0]}' {breach[1]} its hard rule "
                            f"[{envelope.bound_of(breach[0]).lo}, {envelope.bound_of(breach[0]).hi}]"),
                    witness=witness,
                    final_state={var: iv.as_tuple() for var, iv in state.items()},
                )

        return ProofResult(
            verdict=Verdict.SAFE,
            reason="all state variables proven inside hard-rule boundaries for the full parameter space",
            final_state={var: iv.as_tuple() for var, iv in state.items()},
        )

    # -- internals ---------------------------------------------------------------

    def _unknown(self, reason: str) -> ProofResult:
        return ProofResult(verdict=Verdict.UNKNOWN, reason=reason)

    def _apply_effect(self, step, effect: Effect, state: Dict[str, Interval],
                      envelope: Envelope) -> Optional[ProofResult]:
        try:
            param = step.amount_of(effect)
        except KeyError as exc:
            return self._unknown(str(exc))
        if param.lo < -EPS:
            return self._unknown(f"step '{step.id}' param '{param.name}' has negative lower bound; "
                                 f"spend/credit semantics are ambiguous")
        variable = effect.variable
        if variable not in state:
            return self._unknown(f"effect targets untracked variable '{variable}' "
                                 f"(no hard bound declared)")
        amount = _interval_of(param)
        if effect.kind == EffectKind.SPEND:
            state[variable] = state[variable].sub(amount)
            total = envelope.bound_of("spend_total_usd")
            if total is not None:
                state["spend_total_usd"] = state["spend_total_usd"].add(amount)
        elif effect.kind == EffectKind.CREDIT:
            state[variable] = state[variable].add(amount)
        elif effect.kind == EffectKind.SET:
            state[variable] = amount
        else:  # pragma: no cover - EffectKind is closed
            return self._unknown(f"unknown effect kind '{effect.kind}'")
        return None

    def _check_bounds(self, state: Dict[str, Interval],
                      envelope: Envelope) -> Optional[Tuple[str, str]]:
        for var, interval in state.items():
            bound = envelope.bound_of(var)
            if bound is None:
                continue
            breach = interval.violates(bound)
            if breach is not None:
                self.last_violation = (var, breach)
                return (var, breach)
        return None

    def _build_witness(self, plan: Plan, step_id: str, breach: Tuple[str, str],
                       state: Dict[str, Interval], envelope: Envelope) -> Witness:
        """Concrete counterexample: every spend up to the breaching step at its
        maximum — for the whitelisted algebra this reproduces exactly the
        interval that breached."""
        params: Dict[str, float] = {}
        for step in plan.steps:
            for effect in step.effects:
                if effect.kind == EffectKind.SPEND:
                    try:
                        param = step.amount_of(effect)
                    except KeyError:
                        continue
                    params[param.name] = param.hi
            if step.id == step_id:
                break
        variable, kind = breach
        bound = envelope.bound_of(variable)
        observed = state[variable].as_tuple()
        return Witness(
            step_id=step_id,
            variable=variable,
            breach=kind,  # type: ignore[arg-type]
            observed_interval=observed,
            hard_bound=bound.as_tuple() if bound else (0.0, 0.0),
            params=params,
        )


# ---------------------------------------------------------------------------
# Shadow sandbox (Monte-Carlo)
# ---------------------------------------------------------------------------


class ShadowSandbox:
    """Empirical complement to the proof: 200 seeded roll-forwards."""

    def __init__(self, runs: int = DEFAULT_SANDBOX_RUNS, seed: int = DEFAULT_SANDBOX_SEED) -> None:
        self.runs = runs
        self.seed = seed

    def simulate(self, plan: Plan, envelope: Envelope,
                 initial_state: Dict[str, float]) -> SandboxResult:
        rng = random.Random(self.seed)
        violations = 0
        for _ in range(self.runs):
            if not self._roll_forward(plan, envelope, initial_state, rng):
                violations += 1
        confidence = (self.runs - violations) / self.runs if self.runs else 0.0
        return SandboxResult(
            runs=self.runs,
            violations=violations,
            confidence=round(confidence, 6),
            seed=self.seed,
        )

    def _roll_forward(self, plan: Plan, envelope: Envelope,
                      initial_state: Dict[str, float], rng: random.Random) -> bool:
        state = dict(initial_state)
        for step in plan.steps:
            if step.action not in envelope.allowed_actions:
                return False
            for effect in step.effects:
                try:
                    param = step.amount_of(effect)
                except KeyError:
                    return False
                if param.lo < -EPS:
                    return False
                amount = rng.uniform(param.lo, param.hi)
                variable = effect.variable
                if variable not in state and envelope.bound_of(variable) is None:
                    return False
                state.setdefault(variable, 0.0)
                if effect.kind == EffectKind.SPEND:
                    state[variable] -= amount
                    if envelope.bound_of("spend_total_usd") is not None:
                        state["spend_total_usd"] = state.get("spend_total_usd", 0.0) + amount
                elif effect.kind == EffectKind.CREDIT:
                    state[variable] += amount
                elif effect.kind == EffectKind.SET:
                    state[variable] = amount
                for var in (variable, "spend_total_usd"):
                    bound = envelope.bound_of(var)
                    if bound is not None and not bound.contains(state[var]):
                        return False
        return True
