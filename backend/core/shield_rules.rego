package avaira.shield

default allow = false

# Hierarchical & Composable Risk Envelopes v2
# Supports financial limits, action boundaries, and data access controls.

allow {
    not any_violation
}

any_violation {
    violation_unauthorized_action
}

any_violation {
    violation_domain_blocked
}

any_violation {
    violation_spend_limit
}

any_violation {
    violation_data_exfiltration
}

any_violation {
    violation_time_window
}

# 1. Action Whitelisting (Hierarchical)
violation_unauthorized_action {
    action := input.intent.action
    # Check parent and child allowed actions
    allowed := combined_allowed_actions
    not count({x | allowed[x] == action}) > 0
}

combined_allowed_actions = res {
    parent := object.get(input.risk_envelope, "parent_allowed_actions", [])
    child := object.get(input.risk_envelope, "allowed_actions", [])
    res := array.concat(parent, child)
}

# 2. Domain & Data Firewall
violation_domain_blocked {
    target := input.intent.target
    blocked := input.risk_envelope.blocked_actions
    count({x | blocked[x] == target}) > 0
}

violation_data_exfiltration {
    # Block tool calls that try to access sensitive local files or env vars
    params := object.get(input.intent, "parameters", {})
    path := object.get(params, "path", "")
    regex.match(`^(/etc/|/var/|.*\.env|.*key.*)`, path)
}

# 3. Spend Caps (Additive across hierarchy)
violation_spend_limit {
    limit := object.get(input.risk_envelope, "max_spend_usd", 0)
    input.intent.estimated_value > limit
}

# 4. Time Windows (Temporal Logic)
# window format: {"start_hour": 9, "end_hour": 17, "timezone": "UTC"}
violation_time_window {
    window := object.get(input.risk_envelope, "allowed_time_window", null)
    window != null

    current_hour := input.current_time_hour # 0-23

    is_outside_window(current_hour, window.start_hour, window.end_hour)
}

is_outside_window(hour, start, end) {
    hour < start
}
is_outside_window(hour, start, end) {
    hour > end
}

# 5. Delegation Chains
# Allows an agent to authorize actions if a 'parent' or 'accountant' has delegated authority.
violation_delegation_invalid {
    required_role := object.get(input.risk_envelope, "delegation_required_role", null)
    required_role != null

    # Check if the intent contains a valid delegation proof for the required role
    proof := object.get(input.intent, "delegation_proof", null)
    not proof_is_valid(proof, required_role)
}

proof_is_valid(proof, role) {
    proof.role == role
    proof.signature_valid == true
}
