export interface RiskEnvelope {
  maxTransactionValue: bigint;
  allowedTokens: string[];
  allowedProtocols: string[];
  maxSlippageBps: number;
  maxExecutionsPerHour: number;
  expiresAt?: number;
}

export interface ExecutionIntent {
  action: 'SWAP' | 'TRANSFER' | 'STAKE' | 'LEND' | 'BORROW';
  tokenIn?: string;
  tokenOut?: string;
  amountIn: bigint;
  slippageBps?: number;
  protocol?: string;
  metadata?: Record<string, unknown>;
}

export interface AvairaScore {
  raw: number;
  grade: 'A+' | 'A' | 'B' | 'C' | 'D';
  breakdown: {
    successRate: number;
    behaviorConsistency: number;
    collateralRatio: number;
    missionComplexity: number;
    timeOnNetwork: number;
    deviationPenalty: number;
  };
  trend: 'rising' | 'falling' | 'stable';
  updatedAt: number;
}

export interface ValidationResult {
  passed: boolean;
  combinedScore: number;
  semanticScore: number;
  ruleScore: number;
  recommendation: 'APPROVE' | 'REVIEW' | 'REJECT';
  reasoning: string;
  riskFlags: string[];
  fallbackUsed: boolean;
}

export interface AgentRegistration {
  missionGoal: string;
  collateral: bigint;
  riskEnvelope: RiskEnvelope;
}

export interface Agent {
  id: string;
  address: string;
  missionGoal: string;
  collateral: string;
  status: 'active' | 'frozen' | 'inactive';
  score: AvairaScore;
  registeredAt: number;
}

export interface ExecutionResult {
  id: string;
  agentId: string;
  status: 'pending' | 'approved' | 'completed' | 'rejected';
  validation: ValidationResult;
  txHash?: string;
  createdAt: number;
}

export type Network = 'fuji' | 'mainnet' | 'local';
