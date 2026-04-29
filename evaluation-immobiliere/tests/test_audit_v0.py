from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.audit import append_audit_log


class TestAuditV0(unittest.TestCase):
    def test_append_audit_log_uses_fixed_timestamp_when_present(self) -> None:
        old_value = os.environ.get("RUNTIME_FIXED_TIMESTAMP_UTC")
        os.environ["RUNTIME_FIXED_TIMESTAMP_UTC"] = "2026-04-28T00:00:00+00:00"
        try:
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "audit.jsonl"
                append_audit_log(path, {"event": "test"})
                record = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(record["timestamp_utc"], "2026-04-28T00:00:00+00:00")
        finally:
            if old_value is None:
                os.environ.pop("RUNTIME_FIXED_TIMESTAMP_UTC", None)
            else:
                os.environ["RUNTIME_FIXED_TIMESTAMP_UTC"] = old_value


if __name__ == "__main__":
    unittest.main()
