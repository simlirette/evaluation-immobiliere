from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

CLAUDE_PIPELINE_AGENT_CONFIGS = [
    "AGENTCONFIG-DATA-FACTS-V0.yaml",
    "AGENTCONFIG-COMPS-MARKET-V0.yaml",
    "AGENTCONFIG-VALUATION-DRAFT-V0.yaml",
    "AGENTCONFIG-COMPLIANCE-QA-V0.yaml",
    "AGENTCONFIG-REDACTION-V0.yaml",
]
