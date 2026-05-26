from __future__ import annotations


class AgentConfigError(ValueError):
    pass


class ToolPermissionError(PermissionError):
    pass


class ToolResultPairingError(RuntimeError):
    pass
