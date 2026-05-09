import { AgentService }      from './agents';
import { ExecutionService }  from './executions';
import { ReputationService } from './reputation';
import { Network }           from './types';
import { NetworkError }      from './errors';
import { withRetry }         from './utils/retry';

export interface AvairaClientConfig {
  /** API base URL. Defaults to https://api.avaira.xyz */
  apiUrl?: string;
  /** Agent operator private key (0x-prefixed) */
  privateKey?: `0x${string}`;
  /** Target network */
  network: Network;
  /** RPC URL override */
  rpcUrl?: string;
  /** Request timeout in ms (default 30000) */
  timeout?: number;
}

const NETWORK_DEFAULTS: Record<Network, { apiUrl: string; rpcUrl: string }> = {
  mainnet: {
    apiUrl: 'https://api.avaira.xyz',
    rpcUrl: 'https://api.avax.network/ext/bc/C/rpc',
  },
  fuji: {
    apiUrl: 'https://api-fuji.avaira.xyz',
    rpcUrl: 'https://api.avax-test.network/ext/bc/C/rpc',
  },
  local: {
    apiUrl: 'http://localhost:8001',
    rpcUrl: 'http://localhost:8545',
  },
};

export class AvairaClient {
  public readonly agents:     AgentService;
  public readonly executions: ExecutionService;
  public readonly reputation: ReputationService;

  private readonly baseUrl: string;
  private readonly timeout: number;

  constructor(config: AvairaClientConfig) {
    const defaults = NETWORK_DEFAULTS[config.network];
    this.baseUrl = (config.apiUrl ?? defaults.apiUrl).replace(/\/$/, '');
    this.timeout = config.timeout ?? 30_000;

    this.agents     = new AgentService(this);
    this.executions = new ExecutionService(this);
    this.reputation = new ReputationService(this);
  }

  /**
   * Internal fetch wrapper with retry, timeout, and error normalization.
   * @internal
   */
  async _fetch<T>(path: string, init?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    return withRetry(async () => {
      const controller = new AbortController();
      const tid = setTimeout(() => controller.abort(), this.timeout);
      let res: Response;
      try {
        res = await fetch(url, { ...init, signal: controller.signal });
      } catch (err: any) {
        throw new NetworkError(`Request to ${path} failed: ${err.message}`);
      } finally {
        clearTimeout(tid);
      }
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        const msg = body?.error?.message ?? body?.detail ?? `HTTP ${res.status}`;
        throw new NetworkError(`${path}: ${msg}`);
      }
      return res.json() as Promise<T>;
    });
  }
}
