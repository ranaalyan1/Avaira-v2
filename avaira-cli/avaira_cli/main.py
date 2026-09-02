import sys
import subprocess
import json
import os
from typing import List
from backend.core.policy_engine import PolicyEngine
from backend.core.execution_verifier import ExecutionVerifier

def run_cli():
    """
    Avaira Wrapper CLI: avaira run <command...> or avaira verify <certificate_path>
    """
    args = sys.argv[1:]
    if not args:
        print("Avaira CLI - Developer Wrapper")
        print("Usage:")
        print("  avaira run python agent.py")
        print("  avaira verify certificate.json")
        sys.exit(0)

    subcommand = args[0]

    if subcommand == "run":
        cmd_to_run = args[1:]
        if not cmd_to_run:
            print("Error: No target command specified for 'avaira run'")
            sys.exit(1)

        print(f"[AVAIRA GATEKEEPER] Intercepting execution: {' '.join(cmd_to_run)}")
        policy_engine = PolicyEngine()

        # Pre-execution check
        intent_check = policy_engine.evaluate_intent({
            "action": "execute_process",
            "resource": cmd_to_run[0],
            "params": {"args": cmd_to_run[1:]}
        })

        if intent_check.decision == "BLOCK":
            print(f"[AVAIRA KILL-SWITCH ACTIVATED] Execution Blocked!")
            print(f"Reason: {intent_check.reason}")
            sys.exit(1)

        print(f"[AVAIRA POLICY] Action Cleared: {intent_check.decision}")
        print(f"[AVAIRA RUNTIME] Executing sub-process...")

        # Run process
        result = subprocess.run(cmd_to_run)

        # Generate execution proof certificate
        verifier = ExecutionVerifier()
        cert = verifier.build_state_chain("cli_agent", [
            {"action": "INTERCEPT", "resource": cmd_to_run[0]},
            {"action": "POLICY_CHECK", "resource": intent_check.decision},
            {"action": "PROCESS_EXEC", "resource": f"exit_code_{result.returncode}"}
        ])

        cert_file = "avaira_verification_certificate.json"
        with open(cert_file, "w") as f:
            f.write(cert.model_dump_json(indent=2))

        print(f"[AVAIRA PROOF] Provenance chain recorded to {cert_file}")
        sys.exit(result.returncode)

    elif subcommand == "verify":
        cert_path = args[1] if len(args) > 1 else "avaira_verification_certificate.json"
        if not os.path.exists(cert_path):
            print(f"Error: Certificate file '{cert_path}' not found.")
            sys.exit(1)

        with open(cert_path, "r") as f:
            cert_data = json.load(f)

        verifier = ExecutionVerifier()
        # Verify
        from backend.core.execution_verifier import VerificationCertificate
        try:
            cert = VerificationCertificate(**cert_data)
            is_valid = verifier.verify_certificate(cert)
            if is_valid:
                print(f"[AVAIRA VERIFIER] Verification SUCCESS. Certificate {cert.certificate_id} is cryptographically valid.")
                sys.exit(0)
            else:
                print(f"[AVAIRA VERIFIER] Verification FAILED. Certificate signature or state chain is tampered!")
                sys.exit(1)
        except Exception as e:
            print(f"[AVAIRA VERIFIER] Verification ERROR: {e}")
            sys.exit(1)

    else:
        print(f"Unknown command: {subcommand}")
        sys.exit(1)

if __name__ == "__main__":
    run_cli()
