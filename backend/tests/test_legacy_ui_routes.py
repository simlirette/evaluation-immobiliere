"""Regression tests for removed runtime HTML pages."""
from __future__ import annotations

import sys
from email.message import Message
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import api


def _handler(path: str) -> api.RuntimeApiHandler:
    handler = api.RuntimeApiHandler.__new__(api.RuntimeApiHandler)
    handler.path = path
    handler.headers = Message()
    handler._send_json = MagicMock()
    return handler


@pytest.mark.parametrize("path", ["/", "/product", "/product/ui", "/app"])
def test_backend_shell_routes_return_api_index(path):
    handler = _handler(path)

    handler._handle_get()

    handler._send_json.assert_called_once()
    status, payload = handler._send_json.call_args.args
    assert status == 200
    assert payload["schema_version"] == "runtime_api_index_v1"
    assert payload["ui"] == "Next.js frontend"
    assert payload["endpoints"]["health"] == "/health"


@pytest.mark.parametrize(
    "path",
    [
        "/ui",
        "/ops/ui",
        "/ops/cockpit",
        "/review/ui",
        "/evaluateur",
        "/evaluateur/revue",
        "/auth/client.js",
    ],
)
def test_removed_runtime_html_routes_return_410(path):
    handler = _handler(path)

    handler._handle_get()

    handler._send_json.assert_called_once()
    status, payload = handler._send_json.call_args.args
    assert status == 410
    assert payload["code"] == "LEGACY_UI_REMOVED"
    assert payload["path"] == path
