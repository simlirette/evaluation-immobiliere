from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import api  # noqa: E402


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate eval-immo backend deploy readiness.")
    parser.add_argument("--production", action="store_true", help="force production-grade checks")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    parser.add_argument("--no-fs-probe", action="store_true", help="skip filesystem write probes")
    return parser.parse_args(argv)


def _print_human(status: dict[str, object]) -> None:
    print(f"status: {status['status']}")
    print(f"production: {status['production']}")
    print(f"sessions_dir: {status['sessions_dir']}")
    print(f"data_cache_dir: {status['data_cache_dir']}")
    for check in status["checks"]:
        item = check if isinstance(check, dict) else {}
        print(f"- {item.get('status', 'unknown').upper()} {item.get('name', 'unknown')}: {item.get('message', '')}")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.production:
        os.environ.setdefault("APP_ENV", "production")

    status = api.deploy_readiness_status(probe_filesystem=not args.no_fs_probe)
    if args.json:
        print(json.dumps(status, ensure_ascii=False, indent=2))
    else:
        _print_human(status)
    return 0 if status["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
