import type { AvairaClient }   from './client';
import type { ExecutionIntent, ExecutionResult, ValidationResult } from './types';
import { ValidationError } from './errors';

export class ExecutionService {
  constructor(private readonly client: AvairaClient) {}

  /**
   * Validate an intent without executing it.
   * @example
   * const v = await avaira.executions.validate({
   *   agentId: agent.id,
   *   intent: { action: 'SWAP', tokenIn: 'AVAX', tokenOut: 'USDC', amountIn: 500000000000000000n },
   * });
   * if (v.passed) console.log('Safe to execute');
   */
  async validate(params: { agentId: string; intent: ExecutionIntent }): Promise<ValidationResult> {
    if (!params.agentId) throw new ValidationError('agentId is required');
    return this.client._fetch<ValidationResult>('/api/validate/intent', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        agent_id: params.agentId,
        intent: {
          action: params.intent.action.toLowerCase(),
          token_in: params.intent.tokenIn,
          token_out: params.intent.tokenOut,
          value: Number(params.intent.amountIn) / 1e18,
          slippage_bps: params.intent.slippageBps ?? 0,
          protocol: params.intent.protocol ?? '',
        },
      }),
    });
  }

  /**
   * Submit an intent for validation and execution.
   * @example
   * const result = await avaira.executions.submit({
   *   agentId: agent.id,
   *   intent: { action: 'SWAP', tokenIn: 'AVAX', tokenOut: 'USDC', amountIn: 500000000000000000n, slippageBps: 100 },
   * });
   */
  async submit(params: { agentId: string; intent: ExecutionIntent }): Promise<ExecutionResult> {
    if (!params.agentId) throw new ValidationError('agentId is required');
    return this.client._fetch<ExecutionResult>('/api/executions/request', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        agent_id: params.agentId,
        action: params.intent.action.toLowerCase(),
        value: Number(params.intent.amountIn) / 1e18,
        data: '',
        chain_id: '43114',
      }),
    });
  }

  /**
   * Get execution history for an agent.
   */
  async list(agentId: string, limit = 20): Promise<ExecutionResult[]> {
    return this.client._fetch<ExecutionResult[]>(
      `/api/executions?agent_id=${agentId}&limit=${limit}`
    );
  }
}
