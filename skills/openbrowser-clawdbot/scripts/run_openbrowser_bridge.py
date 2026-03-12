#!/usr/bin/env python3
"""Thin wrapper so external agents can invoke the OpenBrowser bridge from the skill."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from server.clawdbot_bridge import main


if __name__ == "__main__":
    raise SystemExit(main())
