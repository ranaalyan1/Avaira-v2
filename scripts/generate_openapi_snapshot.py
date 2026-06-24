import json
import sys
import os

# Set dummy environment variables to pass validation
os.environ["MONGO_URL"] = "mongodb://localhost:27017"
os.environ["DB_NAME"] = "avaira_v2"
os.environ["AVAIRA_LOG_SECRET"] = "secure_key_123456789012345678901234567890"
os.environ["PERMIT_SECRET"] = "secure_key_123456789012345678901234567890"
os.environ["AVAIRA_ADMIN_KEY"] = "secure_key_123456789012345678901234567890"

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from server import app

def generate_openapi():
    openapi_schema = app.openapi()
    # Remove version and other dynamic fields if necessary for stable comparison
    # But for a snapshot, keeping it all is usually fine if we only compare once at the end.
    with open("openapi_snapshot.json", "w") as f:
        json.dump(openapi_schema, f, indent=2)
    print("Generated openapi_snapshot.json")

if __name__ == "__main__":
    generate_openapi()
