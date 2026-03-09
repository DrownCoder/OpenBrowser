#!/usr/bin/env python3
"""Check OpenBrowser readiness status.

Verifies that the OpenBrowser server is running, the Chrome extension
is connected, and LLM API key is configured.

Usage:
    python check_status.py
    python check_status.py --json
"""

import argparse
import json
import sys
from urllib.request import urlopen, Request
from urllib.error import URLError


def check_server(base_url: str) -> dict:
    """Check if server is running."""
    try:
        req = Request(f"{base_url}/health")
        with urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except URLError:
        return {"status": "not_running", "error": "Server not reachable"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def check_extension(base_url: str) -> dict:
    """Check if Chrome extension is connected."""
    try:
        req = Request(f"{base_url}/api")
        with urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return {
                "connected": data.get("websocket_connected", False),
                "connections": data.get("websocket_connections", 0)
            }
    except Exception as e:
        return {"connected": False, "error": str(e)}


def check_llm_config(base_url: str) -> dict:
    """Check if LLM API key is configured."""
    try:
        req = Request(f"{base_url}/api/config/llm")
        with urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            config = data.get("config", {})
            return {
                "configured": config.get("has_api_key", False),
                "model": config.get("model"),
                "base_url": config.get("base_url")
            }
    except Exception as e:
        return {"configured": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Check OpenBrowser readiness")
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8765",
        help="OpenBrowser server URL (default: http://127.0.0.1:8765)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )
    args = parser.parse_args()

    results = {
        "server": check_server(args.url),
        "extension": check_extension(args.url),
        "llm_config": check_llm_config(args.url)
    }

    # Determine overall status
    all_ready = (
        results["server"].get("status") == "healthy" and
        results["extension"].get("connected", False) and
        results["llm_config"].get("configured", False)
    )
    results["ready"] = all_ready

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print("=" * 50)
        print("OpenBrowser Status Check")
        print("=" * 50)

        # Server status
        if results["server"].get("status") == "healthy":
            print("✅ Server: Running")
        else:
            error = results["server"].get("error", "Unknown error")
            print(f"❌ Server: {error}")

        # Extension status
        if results["extension"].get("connected"):
            conn_count = results["extension"].get("connections", 0)
            print(f"✅ Extension: Connected ({conn_count} connection(s))")
        else:
            error = results["extension"].get("error", "Not connected")
            print(f"❌ Extension: {error}")

        # LLM config status
        if results["llm_config"].get("configured"):
            model = results["llm_config"].get("model", "unknown")
            print(f"✅ LLM Config: {model}")
        else:
            error = results["llm_config"].get("error", "API key not configured")
            print(f"❌ LLM Config: {error}")

        print("=" * 50)
        if all_ready:
            print("🎉 OpenBrowser is ready to use!")
            sys.exit(0)
        else:
            print("⚠️  OpenBrowser is NOT ready. Please fix the issues above.")
            sys.exit(1)

    sys.exit(0 if all_ready else 1)


if __name__ == "__main__":
    main()
