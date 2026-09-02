from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import re

class PolicyRule(BaseModel):
    rule_id: str
    action: str  # e.g. "delete", "drop", "transfer", "*"
    resource: str  # e.g. "prod_db", "treasury", "*"
    effect: str  # "DENY", "ALLOW", "WARN"
    condition: Optional[Dict[str, Any]] = None

class PolicyEvaluationResult(BaseModel):
    decision: str  # "ALLOW", "BLOCK", "WARN"
    rule_id: Optional[str] = None
    reason: str
    action: str
    resource: str

class PolicyEngine:
    """
    Pre-execution interceptor (Kill-Switch Policy Engine).
    Evaluates agent intents against JSON-based safety policy rules before execution.
    """
    def __init__(self, default_policies: Optional[List[PolicyRule]] = None):
        self.rules: List[PolicyRule] = default_policies or [
            PolicyRule(
                rule_id="kill-switch-db",
                action="delete",
                resource="prod_db",
                effect="DENY"
            ),
            PolicyRule(
                rule_id="destructive-action-shield",
                action="drop",
                resource="*",
                effect="DENY"
            ),
            PolicyRule(
                rule_id="financial-cap-guard",
                action="transfer",
                resource="treasury",
                effect="DENY",
                condition={"max_amount": 1000}
            )
        ]

    def add_rule(self, rule: PolicyRule):
        self.rules.append(rule)

    def evaluate_intent(self, intent: Dict[str, Any]) -> PolicyEvaluationResult:
        """
        Evaluates an agent intent payload.
        Intent structure expected: {"action": str, "resource": str, "amount": float/int (optional), "params": dict (optional)}
        """
        action = intent.get("action", "").lower()
        resource = intent.get("resource", "").lower()
        amount = intent.get("amount", 0)

        for rule in self.rules:
            rule_action = rule.action.lower()
            rule_resource = rule.resource.lower()

            action_match = (rule_action == "*") or (rule_action == action)
            resource_match = (rule_resource == "*") or (rule_resource == resource)

            if action_match and resource_match:
                # Check condition if present
                if rule.condition:
                    max_amount = rule.condition.get("max_amount")
                    if max_amount is not None and amount > max_amount:
                        if rule.effect == "DENY":
                            return PolicyEvaluationResult(
                                decision="BLOCK",
                                rule_id=rule.rule_id,
                                reason=f"Triggered policy '{rule.rule_id}': amount ${amount} exceeds limit ${max_amount}",
                                action=action,
                                resource=resource
                            )
                else:
                    if rule.effect == "DENY":
                        return PolicyEvaluationResult(
                            decision="BLOCK",
                            rule_id=rule.rule_id,
                            reason=f"Triggered kill-switch policy '{rule.rule_id}' blocking action '{action}' on '{resource}'",
                            action=action,
                            resource=resource
                        )
                    elif rule.effect == "WARN":
                        return PolicyEvaluationResult(
                            decision="WARN",
                            rule_id=rule.rule_id,
                            reason=f"Policy warning '{rule.rule_id}' for action '{action}' on '{resource}'",
                            action=action,
                            resource=resource
                        )

        return PolicyEvaluationResult(
            decision="ALLOW",
            reason="Intent cleared all pre-execution policy checks",
            action=action,
            resource=resource
        )
