import type { AvairaClient } from './client';
import type { AvairaScore }  from './types';
import { ValidationError }   from './errors';

export class ReputationService {
  constructor(private readonly client: AvairaClient) {}

  /**
   * Get the Avaira score for an agent.
   * @example
   * const score = await avaira.reputation.getScore('agent-id');
   * console.log(`${score.grade} (${score.raw}/100)`);
   */
  async getScore(agentId: string): Promise<AvairaScore> {
    if (!agentId) throw new ValidationError('agentId is required');
    const raw = await this.client._fetch<any>(`/api/agents/${agentId}/score`);
    return {
      raw:   raw.score ?? 0,
      grade: raw.grade ?? 'D',
      breakdown: raw.breakdown ?? {
        successRate: 0, behaviorConsistency: 0, collateralRatio: 0,
        missionComplexity: 0, timeOnNetwork: 0, deviationPenalty: 0,
      },
      trend:     raw.trend ?? 'stable',
      updatedAt: raw.updated_at ?? Date.now() / 1000,
    };
  }

  /**
   * Get leaderboard — top agents by score.
   * @example
   * const leaders = await avaira.reputation.leaderboard(10);
   */
  async leaderboard(limit = 10): Promise<AvairaScore[]> {
    return this.client._fetch<AvairaScore[]>(`/api/reputation/leaderboard?limit=${limit}`);
  }

  /**
   * Get reputation history for an agent.
   */
  async history(agentId: string): Promise<any[]> {
    if (!agentId) throw new ValidationError('agentId is required');
    return this.client._fetch<any[]>(`/api/reputation/${agentId}/history`);
  }
}
