package avaira.shield

default allow = false

# Hard mathematical rules for the Execution Shield
# No hallucinations, no exceptions.

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

# 1. Action Whitelisting
violation_unauthorized_action {
    action := input.intent.action
    allowed := input.risk_envelope.allowed_actions
    not count({x | allowed[x] == action}) > 0
}

# 2. Domain Firewall
violation_domain_blocked {
    target := input.intent.target
    blocked := input.risk_envelope.blocked_actions # Reusing this for demo, or a dedicated list
    count({x | blocked[x] == target}) > 0
}

# 3. Deterministic Spend Caps
violation_spend_limit {
    input.intent.estimated_value > input.risk_envelope.max_spend_usd
}
