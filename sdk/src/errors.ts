export class AvairaError extends Error {
  constructor(message: string, public readonly code: string) {
    super(message);
    this.name = 'AvairaError';
  }
}

export class ValidationError  extends AvairaError { constructor(m: string) { super(m, 'VALIDATION_ERROR'); } }
export class NetworkError      extends AvairaError { constructor(m: string) { super(m, 'NETWORK_ERROR'); } }
export class ContractError     extends AvairaError { constructor(m: string) { super(m, 'CONTRACT_ERROR'); } }
export class NotFoundError     extends AvairaError { constructor(m: string) { super(m, 'NOT_FOUND'); } }
export class UnauthorizedError extends AvairaError { constructor(m: string) { super(m, 'UNAUTHORIZED'); } }
export class RateLimitError    extends AvairaError { constructor(m: string) { super(m, 'RATE_LIMITED'); } }
