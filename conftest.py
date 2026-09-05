"""Root pytest configuration.

- Puts `sdk/` on sys.path so `tests/test_sdk_basic.py` can import
  `avaira_shield` when the suite runs from the repository root.
- Provides the environment variables `backend/server.py` requires at import
  (same values CI uses) so the mocked e2e tests can run without a live stack.
"""
from __future__ import annotations

import os
import sys

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
SDK_ROOT = os.path.join(REPO_ROOT, "sdk")

for path in (SDK_ROOT,):
    if path not in sys.path:
        sys.path.insert(0, path)

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "avaira_test")
os.environ.setdefault("PERMIT_SECRET", "test-secret-32-chars-minimum-here")
