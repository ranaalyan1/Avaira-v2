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

# 4. Time Windows
violation_time_window {
    # Example: block actions during maintenance window or outside business hours if configured
    window := object.get(input.risk_envelope, "allowed_time_window", null)
    window != null
    now := input.current_time # Provided by caller
    # Logic to check if now is inside allowed window
}
