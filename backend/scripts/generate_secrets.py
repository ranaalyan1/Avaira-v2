import secrets
import os

def generate_secrets():
    print("--- Avaira Security: Secret Generator ---")

    log_secret = secrets.token_urlsafe(32)
    permit_secret = secrets.token_urlsafe(32)
    admin_key = secrets.token_urlsafe(32)

    print("\nGenerated high-entropy secrets for .env:")
    print(f"AVAIRA_LOG_SECRET={log_secret}")
    print(f"PERMIT_SECRET={permit_secret}")
    print(f"AVAIRA_ADMIN_KEY={admin_key}")

    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        print(f"\nWarning: {env_path} already exists. Please update it manually.")
    else:
        example_path = os.path.join(os.path.dirname(__file__), "..", ".env.example")
        if os.path.exists(example_path):
            with open(example_path, "r") as f:
                content = f.read()

            content = content.replace("REPLACE_WITH_SECURE_32_BYTE_STRING", log_secret)
            content = content.replace("REPLACE_WITH_SECURE_ADMIN_SECRET", admin_key)
            content = content.replace("REPLACE_WITH_SECURE_32_BYTE_STRING_FOR_PERMITS", permit_secret)

            with open(env_path, "w") as f:
                f.write(content)
            print(f"\nCreated new {env_path} with generated secrets.")

if __name__ == "__main__":
    generate_secrets()
