import pytest
from backend.core.execution_verifier import ExecutionVerifier

def test_execution_verifier_chain():
    verifier = ExecutionVerifier()
    actions = [
        {"action": "QUERY", "resource": "market_depth", "timestamp": "2025-01-01T10:00:00Z"},
        {"action": "CALCULATE", "resource": "slippage_curve", "timestamp": "2025-01-01T10:00:01Z"},
        {"action": "SWAP", "resource": "usdc_eth", "timestamp": "2025-01-01T10:00:02Z"}
    ]

    cert = verifier.build_state_chain("agent_007", actions)
    assert cert.step_count == 3
    assert cert.steps[0].step_id == "VRF-01"
    assert cert.steps[0].previous_hash == "0" * 64

    # Verify certificate
    is_valid = verifier.verify_certificate(cert)
    assert is_valid is True

def test_execution_verifier_tampered_chain():
    verifier = ExecutionVerifier()
    actions = [
        {"action": "QUERY", "resource": "market_depth", "timestamp": "2025-01-01T10:00:00Z"},
        {"action": "SWAP", "resource": "usdc_eth", "timestamp": "2025-01-01T10:00:02Z"}
    ]
    cert = verifier.build_state_chain("agent_007", actions)

    # Tamper with action
    cert.steps[1].action = "TRANSFER_ALL"
    assert verifier.verify_certificate(cert) is False
