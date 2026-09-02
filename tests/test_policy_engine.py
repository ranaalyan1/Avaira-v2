import pytest
from backend.core.policy_engine import PolicyEngine, PolicyRule

def test_policy_engine_kill_switch():
    engine = PolicyEngine()

    # Test blocked action
    result = engine.evaluate_intent({"action": "delete", "resource": "prod_db"})
    assert result.decision == "BLOCK"
    assert result.rule_id == "kill-switch-db"

    # Test allowed action
    result_allow = engine.evaluate_intent({"action": "read", "resource": "user_logs"})
    assert result_allow.decision == "ALLOW"

def test_policy_engine_financial_threshold():
    engine = PolicyEngine()

    # Over threshold
    res_block = engine.evaluate_intent({"action": "transfer", "resource": "treasury", "amount": 5000})
    assert res_block.decision == "BLOCK"

    # Under threshold
    res_allow = engine.evaluate_intent({"action": "transfer", "resource": "treasury", "amount": 200})
    assert res_allow.decision == "ALLOW"
