# Protocol Fees
PROTOCOL_FEE_RATE = 0.005  # 0.5%
TRUST_POOL_SHARE = 0.75
PROTOCOL_REVENUE_SHARE = 0.25

# Reputation
INITIAL_REPUTATION = 100
REP_SUCCESS_BONUS = 2
REP_FAILURE_PENALTY = 5
REP_FREEZE_PENALTY = 20
REP_SLASH_PENALTY = 10

# Slashing
SLASH_RATE = 0.5  # 50% of collateral

# Grading
AVAIRA_GRADES = [
    ('AAA', 90, 100),
    ('AA', 80, 89),
    ('A', 70, 79),
    ('BBB', 60, 69),
    ('BB', 50, 59),
    ('B', 40, 49),
    ('CCC', 30, 39),
    ('D', 0, 29)
]

# Mission Fee Splits
MISSION_FEE_AGENT = 0.85
MISSION_FEE_UNDERWRITER = 0.10
MISSION_FEE_PROTOCOL = 0.05

# Subscription Tiers
SUBSCRIPTION_TIERS = {
    'free': {'price': 0, 'max_agents': 1, 'features': ['basic_monitoring', 'community_rating']},
    'growth': {'price': 200, 'max_agents': 10, 'features': ['enhanced_monitoring', 'verified_badge', 'priority_support']},
    'enterprise': {'price': 2000, 'max_agents': -1, 'features': ['unlimited_agents', 'custom_risk', 'compliance_reports', 'dedicated_pool']}
}
