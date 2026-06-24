from fastapi import APIRouter, Depends, Query
from app.dependencies import get_db
from app.config import get_settings

router = APIRouter(tags=[])
settings = get_settings()

async def get_treasury_stats_internal(db):
    pipeline = [
        {"$group": {
            "_id": None,
            "total_fees": {"$sum": "$total_fee"},
            "total_trust_pool": {"$sum": "$trust_pool_share"},
            "total_protocol_revenue": {"$sum": "$protocol_revenue_share"},
            "transaction_count": {"$sum": 1}
        }}
    ]
    result = await db.treasury_transactions.aggregate(pipeline).to_list(1)
    if result:
        stats = result[0]
        stats.pop("_id", None)
        return {
            "total_fees": round(stats.get("total_fees", 0), 6),
            "total_trust_pool": round(stats.get("total_trust_pool", 0), 6),
            "total_protocol_revenue": round(stats.get("total_protocol_revenue", 0), 6),
            "transaction_count": stats.get("transaction_count", 0)
        }
    return {"total_fees": 0, "total_trust_pool": 0, "total_protocol_revenue": 0, "transaction_count": 0}

@router.get("/treasury/stats")
async def get_treasury_stats(db=Depends(get_db)):
    return await get_treasury_stats_internal(db)

@router.get("/treasury/transactions")
async def list_treasury_transactions(limit: int = Query(100, ge=1, le=500), db=Depends(get_db)):
    txs = await db.treasury_transactions.find({}, {"_id": 0}).sort("timestamp", -1).to_list(limit)
    return txs

@router.get("/architecture")
async def get_architecture():
    from app.constants import INITIAL_REPUTATION
    # ... static dict from server.py (omitted here for brevity, assume correct copy) ...
    return {
        "contracts": [
            {
                "name": "AgentRegistry",
                "address": settings.AGENT_REGISTRY_ADDRESS or "Not deployed",
                "description": "Central registry for all AI agents. Manages registration, collateral staking, and agent status.",
                "state_variables": [
                    {"name": "agents", "type": "mapping(bytes32 => Agent)", "description": "Agent ID to Agent struct"},
                    {"name": "agentCollateral", "type": "mapping(bytes32 => uint256)", "description": "Agent collateral balances"},
                    {"name": "agentStatus", "type": "mapping(bytes32 => AgentStatus)", "description": "Agent operational status"},
                    {"name": "reputationScores", "type": "mapping(bytes32 => uint256)", "description": "Agent reputation scores"},
                    {"name": "totalAgents", "type": "uint256", "description": "Total registered agents"},
                    {"name": "minCollateral", "type": "uint256", "description": "Minimum collateral required (0.1 USD)"}
                ],
                "functions": [
                    {"name": "registerAgent", "params": "(string name, bytes32 missionHash, RiskEnvelope envelope)", "returns": "bytes32 agentId", "modifier": "payable", "description": "Register new agent with collateral stake"},
                    {"name": "stakeCollateral", "params": "(bytes32 agentId)", "returns": "bool", "modifier": "payable", "description": "Add additional collateral"},
                    {"name": "updateAgentStatus", "params": "(bytes32 agentId, AgentStatus status)", "returns": "bool", "modifier": "onlyProtocol", "description": "Update agent operational status"},
                    {"name": "getAgent", "params": "(bytes32 agentId)", "returns": "Agent memory", "modifier": "view", "description": "Get agent details"},
                    {"name": "isAgentActive", "params": "(bytes32 agentId)", "returns": "bool", "modifier": "view", "description": "Check if agent can execute"}
                ],
                "events": [
                    "AgentRegistered(bytes32 indexed agentId, address indexed owner, uint256 collateral)",
                    "CollateralStaked(bytes32 indexed agentId, uint256 amount, uint256 total)",
                    "AgentStatusUpdated(bytes32 indexed agentId, AgentStatus oldStatus, AgentStatus newStatus)",
                    "ReputationUpdated(bytes32 indexed agentId, uint256 oldScore, uint256 newScore)"
                ]
            },
            {
                "name": "ExecutionWallet",
                "address": settings.EXECUTION_WALLET_ADDRESS or "Not deployed",
                "description": "Verifies EIP-712 signed permits and executes approved transactions. Deducts 0.5% protocol fee.",
                "state_variables": [
                    {"name": "DOMAIN_SEPARATOR", "type": "bytes32", "description": "EIP-712 domain separator"},
                    {"name": "executionNonces", "type": "mapping(bytes32 => uint256)", "description": "Per-agent nonces to prevent replay"},
                    {"name": "protocolFeeRate", "type": "uint256", "description": "Fee rate in basis points (50 = 0.5%)"},
                    {"name": "treasury", "type": "address", "description": "Treasury contract address"},
                    {"name": "registry", "type": "address", "description": "AgentRegistry contract address"},
                    {"name": "permitTypehash", "type": "bytes32", "description": "EIP-712 type hash for permit struct"}
                ],
                "functions": [
                    {"name": "verifyPermitSignature", "params": "(ExecutionPermit permit, bytes signature)", "returns": "bool", "modifier": "view", "description": "Verify EIP-712 permit signature"},
                    {"name": "executeApprovedTransaction", "params": "(ExecutionPermit permit, bytes signature, bytes callData)", "returns": "bool", "modifier": "nonReentrant", "description": "Execute transaction after permit verification"},
                    {"name": "deductProtocolFee", "params": "(uint256 value)", "returns": "uint256 fee", "modifier": "internal", "description": "Calculate and deduct 0.5% fee"},
                    {"name": "sendFeeToTreasury", "params": "(uint256 fee)", "returns": "bool", "modifier": "internal", "description": "Transfer fee to Treasury contract"}
                ],
                "events": [
                    "PermitVerified(bytes32 indexed executionId, bytes32 indexed agentId, bytes32 permitHash)",
                    "TransactionExecuted(bytes32 indexed executionId, bytes32 indexed agentId, uint256 value, uint256 fee)",
                    "FeeDeducted(bytes32 indexed executionId, uint256 fee, uint256 trustPoolShare, uint256 revenueShare)"
                ]
            },
            {
                "name": "FreezeSlash",
                "address": settings.FREEZE_SLASH_ADDRESS or "Not deployed",
                "description": "Emergency freeze and collateral slashing mechanism. Triggered on risk envelope deviation.",
                "state_variables": [
                    {"name": "frozenAgents", "type": "mapping(bytes32 => bool)", "description": "Agent frozen status"},
                    {"name": "slashHistory", "type": "mapping(bytes32 => SlashEvent[])", "description": "Per-agent slash history"},
                    {"name": "slashRate", "type": "uint256", "description": "Default slash rate (50%)"},
                    {"name": "registry", "type": "address", "description": "AgentRegistry contract reference"}
                ],
                "functions": [
                    {"name": "freezeAgent", "params": "(bytes32 agentId, string reason)", "returns": "bool", "modifier": "onlyProtocol", "description": "Instantly freeze agent execution"},
                    {"name": "slashCollateral", "params": "(bytes32 agentId, uint256 amount, string reason)", "returns": "bool", "modifier": "onlyProtocol", "description": "Slash agent collateral"},
                    {"name": "unfreezeAgent", "params": "(bytes32 agentId)", "returns": "bool", "modifier": "onlyGovernance", "description": "Restore agent after review"},
                    {"name": "isAgentFrozen", "params": "(bytes32 agentId)", "returns": "bool", "modifier": "view", "description": "Check freeze status"}
                ],
                "events": [
                    "AgentFrozen(bytes32 indexed agentId, string reason, uint256 timestamp)",
                    "CollateralSlashed(bytes32 indexed agentId, uint256 amount, string reason)",
                    "AgentUnfrozen(bytes32 indexed agentId, uint256 timestamp)"
                ]
            },
            {
                "name": "Treasury",
                "address": settings.TREASURY_ADDRESS or "Not deployed",
                "description": "Receives protocol fees and splits them: 75% to TrustPool, 25% to ProtocolRevenue.",
                "state_variables": [
                    {"name": "trustPoolBalance", "type": "uint256", "description": "Accumulated TrustPool funds"},
                    {"name": "protocolRevenueBalance", "type": "uint256", "description": "Accumulated Protocol Revenue"},
                    {"name": "trustPoolShare", "type": "uint256", "description": "TrustPool share (75%)"},
                    {"name": "revenueShare", "type": "uint256", "description": "Revenue share (25%)"},
                    {"name": "totalFeesReceived", "type": "uint256", "description": "Total lifetime fees"}
                ],
                "functions": [
                    {"name": "receiveFees", "params": "()", "returns": "bool", "modifier": "payable onlyExecutionWallet", "description": "Receive fees from ExecutionWallet"},
                    {"name": "splitFee", "params": "(uint256 amount)", "returns": "(uint256, uint256)", "modifier": "internal", "description": "Split fee into TrustPool and Revenue"},
                    {"name": "withdrawRevenue", "params": "(address to, uint256 amount)", "returns": "bool", "modifier": "onlyGovernance", "description": "Withdraw protocol revenue"},
                    {"name": "getTreasuryStats", "params": "()", "returns": "(uint256, uint256, uint256)", "modifier": "view", "description": "Get treasury balances"}
                ],
                "events": [
                    "FeeReceived(uint256 amount, uint256 trustPool, uint256 revenue)",
                    "RevenueWithdrawn(address indexed to, uint256 amount)",
                    "TrustPoolUpdated(uint256 newBalance)"
                ]
            },
            {
                "name": "ReputationEngine",
                "address": settings.REPUTATION_ENGINE_ADDRESS or "Not deployed",
                "description": "Tracks and updates agent reputation scores based on execution outcomes.",
                "state_variables": [
                    {"name": "scores", "type": "mapping(bytes32 => uint256)", "description": "Agent reputation scores"},
                    {"name": "successBonus", "type": "uint256", "description": "Points gained on success (+2)"},
                    {"name": "failurePenalty", "type": "uint256", "description": "Points lost on failure (-5)"},
                    {"name": "freezePenalty", "type": "uint256", "description": "Points lost on freeze (-20)"},
                    {"name": "maxScore", "type": "uint256", "description": "Maximum reputation (200)"}
                ],
                "functions": [
                    {"name": "increaseScoreOnSuccess", "params": "(bytes32 agentId)", "returns": "uint256", "modifier": "onlyProtocol", "description": "Reward successful execution"},
                    {"name": "decreaseScoreOnFailure", "params": "(bytes32 agentId)", "returns": "uint256", "modifier": "onlyProtocol", "description": "Penalize failed execution"},
                    {"name": "penalizeOnFreeze", "params": "(bytes32 agentId)", "returns": "uint256", "modifier": "onlyProtocol", "description": "Heavy penalty on freeze"},
                    {"name": "getScore", "params": "(bytes32 agentId)", "returns": "uint256", "modifier": "view", "description": "Get current score"}
                ],
                "events": [
                    "ScoreIncreased(bytes32 indexed agentId, uint256 oldScore, uint256 newScore, string reason)",
                    "ScoreDecreased(bytes32 indexed agentId, uint256 oldScore, uint256 newScore, string reason)"
                ]
            },
            {
                "name": "InsurancePool",
                "address": "Not deployed",
                "description": "Compensates backers if agent execution fails and causes losses.",
                "state_variables": [
                    {"name": "poolBalance", "type": "uint256", "description": "Total insurance pool funds"},
                    {"name": "claims", "type": "mapping(bytes32 => Claim[])", "description": "Filed claims"},
                    {"name": "maxClaimRate", "type": "uint256", "description": "Max claim percentage per incident"}
                ],
                "functions": [
                    {"name": "coverBackersIfExecutionFails", "params": "(bytes32 executionId, address[] backers, uint256[] amounts)", "returns": "bool", "modifier": "onlyProtocol", "description": "Process insurance claim"},
                    {"name": "fundPool", "params": "()", "returns": "bool", "modifier": "payable", "description": "Add funds to insurance pool"},
                    {"name": "getPoolBalance", "params": "()", "returns": "uint256", "modifier": "view", "description": "Get current pool balance"}
                ],
                "events": [
                    "ClaimProcessed(bytes32 indexed executionId, uint256 totalPayout, uint256 backerCount)",
                    "PoolFunded(address indexed funder, uint256 amount)"
                ]
            }
        ],
        "security_assumptions": [
            "Permit signer (backend) private key is stored securely in HSM/KMS",
            "EIP-712 domain separator includes chainId to prevent cross-chain replay",
            "Nonces are strictly monotonic per agent to prevent replay attacks",
            "FreezeSlash can be called by protocol-authorized addresses only",
            "Re-entrancy guards on all state-changing functions in ExecutionWallet",
            "Collateral withdrawal requires cooldown period after unstake request"
        ],
        "attack_surfaces": [
            "Permit replay: Mitigated by nonces and deadline timestamps",
            "Front-running: Mitigated by commit-reveal scheme for high-value txs",
            "Signer key compromise: Requires multi-sig rotation mechanism",
            "Flash loan attacks on collateral: Minimum lock period enforced",
            "Griefing via false freeze: onlyProtocol modifier + governance override",
            "MEV extraction: Private mempool submission recommended"
        ],
        "gas_considerations": [
            "Batch agent operations to amortize base gas costs",
            "Use events instead of storage for historical data",
            "Minimize storage writes in hot paths (execution verification)",
            "Consider EIP-2929 access list for frequently accessed storage slots",
            "Proxy pattern for upgradeability without redeployment costs"
        ]
    }

@router.get("/sdk/docs")
async def get_sdk_docs():
    return {
        "sdk_name": "Avaira Python SDK",
        "languages": ["Python"],
        "version": "0.1.0",
        "install": {"python": "pip install avaira-sdk"},
        "functions": [
            {"name": "register", "description": "Register an AI agent with Avaira", "params": [{"name": "name", "type": "string"}, {"name": "goal", "type": "string"}], "returns": "str",
             "example": "agent_id = await avaira.register(name='ResearchBot', goal='Market analysis')"},
            {"name": "run", "description": "Run a task with Avaira protection", "params": [{"name": "task", "type": "string"}, {"name": "execute_fn", "type": "callable"}], "returns": "RunResult",
             "example": "result = await avaira.run(task='Search news', execute_fn=my_fn)"},
            {"name": "validate", "description": "Standalone intent validation", "params": [{"name": "intent", "type": "dict"}], "returns": "ValidationResult",
             "example": "val = await avaira.validate(my_intent)"}
        ],
        "quick_start": "from avaira import AvairaClient, AvairaConfig, RiskEnvelope\n\n# 1. Define boundaries\nenvelope = RiskEnvelope(max_spend_usd=50.0, allowed_actions=['search'])\nconfig = AvairaConfig(api_key='your_api_key', risk_envelope=envelope)\navaira = AvairaClient(config)\n\n# 2. Wrap your agent\nresult = await avaira.run(\n    task='Search for YC news',\n    execute_fn=lambda: my_agent.run('Search for YC news')\n)\n\nprint(result['status'])"
    }

@router.get("/revenue/streams")
async def get_revenue_streams(db=Depends(get_db)):
    from app.constants import SUBSCRIPTION_TIERS
    treasury = await get_treasury_stats_internal(db)
    uw_pipeline = [{"$match": {"type": "underwriting"}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}, "count": {"$sum": 1}}}]
    uw_result = await db.revenue_events.aggregate(uw_pipeline).to_list(1)
    uw_rev = uw_result[0]["total"] if uw_result else 0
    uw_count = uw_result[0]["count"] if uw_result else 0
    slash_events = await db.freeze_events.find({"type": "slash"}, {"_id": 0}).to_list(200)
    slash_rev = sum(e.get("collateral_slashed", 0) * 0.2 for e in slash_events)
    return {
        "streams": [
            {"name": "Transaction Fees", "description": "0.5% on every execution", "amount": round(treasury["total_fees"], 6), "transactions": treasury["transaction_count"], "icon": "zap"},
            {"name": "Underwriting Spread", "description": "5% protocol fee on settled missions", "amount": round(uw_rev, 6), "transactions": uw_count, "icon": "shield"},
            {"name": "Slashing Revenue", "description": "20% of slashed collateral", "amount": round(slash_rev, 6), "transactions": len(slash_events), "icon": "scissors"},
            {"name": "Data & Analytics", "description": "API queries and insights subscriptions", "amount": 0, "transactions": 0, "icon": "database"}
        ],
        "total_revenue": round(treasury["total_fees"] + uw_rev + slash_rev, 6),
        "subscription_tiers": SUBSCRIPTION_TIERS
    }
