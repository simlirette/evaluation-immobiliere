#!/usr/bin/env python3
from __future__ import annotations

from urllib import request
import argparse
import json


def post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Demarre une execution runtime via l'API v0.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8787")
    parser.add_argument("--fixture", default="case_nominal.json")
    args = parser.parse_args()

    session = post_json(f"{args.base_url}/session", {"strict_mode": True})
    result = post_json(f"{args.base_url}/start", {"session_id": session["session_id"], "fixture": args.fixture})
    runtime = result["result"]

    print(f"Session: {session['session_id']}")
    print(f"Dossier: {runtime['dossier_id']}")
    print(f"Status: {runtime['status']}")
    print(f"Events SSE: {args.base_url}{result['session']['events_url']}")
    print(f"Artifacts: {runtime['artifact_dir']}")


if __name__ == "__main__":
    main()
