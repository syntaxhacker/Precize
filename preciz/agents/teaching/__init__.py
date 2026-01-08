"""Teaching/Content Generation Agent.

Generates long-form educational content with progressive difficulty
and zero-to-expert buildup.
"""

from .orchestrator import (
    DocumentOrchestrator,
    GenerateTool,
    AppendTool,
    ReviewTool,
    ImproveTool,
    SummaryTool,
    BlockTask,
    OrchestrationState,
    generate_long_document,
)
from .preferences import ContentPreferences

__all__ = [
    "DocumentOrchestrator",
    "GenerateTool",
    "AppendTool",
    "ReviewTool",
    "ImproveTool",
    "SummaryTool",
    "BlockTask",
    "OrchestrationState",
    "generate_long_document",
    "ContentPreferences",
]
