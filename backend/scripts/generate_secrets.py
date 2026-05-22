import secrets
import os

def generate():
    log_secret = secrets.token_urlsafe(32)
    admin_key = secrets.token_urlsafe(32)

    print("-" * 60)
    print("AVAIRA V2 SECRET GENERATOR")
    print("-" * 60)
    print(f"AVAIRA_LOG_SECRET={log_secret}")
    print(f"AVAIRA_ADMIN_KEY={admin_key}")
    print("-" * 60)
    print("Copy these into your backend/.env file.")
    print("Keep these values secret. They are used for encryption and admin access.")
    print("-" * 60)

if __name__ == "__main__":
    generate()
