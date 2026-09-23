"""Three-agent pipeline: Step → Discovery → Test & Report."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.agents.orchestrator import AgentOrchestrator, OrchestratorResult

__all__ = ["AgentOrchestrator", "OrchestratorResult"]


def __getattr__(name: str):
    if name == "AgentOrchestrator":
        from src.agents.orchestrator import AgentOrchestrator

        return AgentOrchestrator
    if name == "OrchestratorResult":
        from src.agents.orchestrator import OrchestratorResult

        return OrchestratorResult
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
