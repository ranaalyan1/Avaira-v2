# Avaira Security Architecture

Avaira is designed to provide high-assurance execution control for autonomous AI agents. Our security model focuses on integrity, non-repudiation, and automated risk mitigation.

## 1. Tamper-Evident Intent Logging

Every execution intent submitted by an agent is logged using a cryptographic hash chain.

- **Chaining:** Each log entry contains `SHA-256(intent + agent_id + timestamp + risk_envelope_hash + prev_entry_hash)`.
- **Integrity Guarantee:** Any modification to a past log entry will result in a hash mismatch for all subsequent entries.
- **Verification:** The `IntentLogger.verify_chain()` method allows users to audit the full history of an agent and detect any server-side or client-side tampering.

## 2. API Key Management

- **Generation:** API keys are cryptographically secure random strings generated at registration.
- **Scope:** Keys are scoped to a specific `agent_id`.
- **Transmission:** All SDK calls must include the key in the `X-Avaira-API-Key` header. TLS is mandatory for all production endpoints.

## 3. Execution Shield Pipeline

To prevent prompt injection and "jailbreaking" of an agent's risk envelope, every intent passes through the **Execution Shield**:

1.  **Local SLM Intercept:** An ultra-fast, local Small Language Model (phi-3) performs initial intent classification and risk detection with <50ms latency.
2.  **Deterministic OPA Rules:** A non-probabilistic Open Policy Agent (Rego) engine enforces hard mathematical limits (domain whitelisting, spend caps).
3.  **Neural Audit:** A final two-pass LLM check (Claude 3.5 Sonnet) for deep adversarial review and scope creep detection.

## 4. Software Slashing & Suspension

When a deviation is detected (either by the validator or by comparing execution outcomes), the `SlashEngine` performs the following:

- **Circuit Breaker:** The agent's status is set to `suspended`, immediately rejecting all further API calls.
- **Evidence Preservation:** A unique `slash_id` and evidence hash are generated and logged.
- **Human-in-the-loop:** Suspension can only be lifted through a successful appeal or admin override.

## 5. Trusted Execution & Virtual Vaults

- **TEE Proof-of-Execution:** Avaira's core logic is containerized to run within AWS Nitro Enclaves, providing cryptographic attestation that the execution shield was not tampered with.
- **AgentVault (Virtual Fiat):** For chainless operation, Avaira generates single-use virtual credit cards with programmatically locked spend limits, creating a physical fiat wall against rogue spend loops.

## Reporting Vulnerabilities

If you discover a security vulnerability in Avaira, please contact our security team at security@avaira.xyz. We participate in a bug bounty program for critical vulnerabilities.
