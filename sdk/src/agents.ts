import type { AvairaClient } from './client';
import type { Agent, AgentRegistration } from './types';
import { ValidationError } from './errors';

export class AgentService {
  constructor(private readonly client: AvairaClient) {}

  /**
   * Register a new agent with collateral and risk envelope.
   * @example
   * const agent = await avaira.agents.register({
   *   missionGoal: 'DeFi arbitrage within declared parameters',
   *   collateral: 1_000_000_000_000_000_000n,
   *   riskEnvelope: {
   *     maxTransactionValue: 10_000_000_000_000_000_000n,
   *     allowedTokens: ['AVAX', 'USDC'],
   *     allowedProtocols: ['traderjoe'],
   *     maxSlippageBps: 200,
   *     maxExecutionsPerHour: 10,
   *   },
   * });
   */
  async register(params: AgentRegistration): Promise<Agent> {
    if (!params.missionGoal?.trim()) throw new ValidationError('missionGoal is required');
    if (params.collateral <= 0n)     throw new ValidationError('collateral must be > 0');

    return this.client._fetch<Agent>('/api/agents/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mission_intent: params.missionGoal,
        collateral_amount: Number(params.collateral) / 1e18,
        risk_envelope: {
          max_tx_value: Number(params.riskEnvelope.maxTransactionValue) / 1e18,
          allowed_actions: params.riskEnvelope.allowedTokens,
          max_slippage: params.riskEnvelope.maxSlippageBps,
          max_daily_txns: params.riskEnvelope.maxExecutionsPerHour * 24,
        },
        wallet_address: '0x0000000000000000000000000000000000000000',
        name: params.missionGoal.slice(0, 40),
      }),
    });
  }

  /**
   * Get an agent by ID.
   */
  async get(agentId: string): Promise<Agent> {
    if (!agentId) throw new ValidationError('agentId is required');
    return this.client._fetch<Agent>(`/api/agents/${agentId}`);
  }

  /**
   * List all registered agents.
   */
  async list(limit = 20, offset = 0): Promise<Agent[]> {
    return this.client._fetch<Agent[]>(`/api/agents?limit=${limit}&offset=${offset}`);
  }
}
