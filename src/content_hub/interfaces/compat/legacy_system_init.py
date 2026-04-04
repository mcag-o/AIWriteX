from __future__ import annotations

from src.ai_write_x.core.tool_registry import GlobalToolRegistry
from src.ai_write_x.tools.custom_tool import AIForgeSearchTool
from src.ai_write_x.tools.custom_tool import ReadTemplateTool

from content_hub.interfaces.compat.legacy_workflow import UnifiedContentWorkflow


def initialize_global_tools():
    registry = GlobalToolRegistry.get_instance()
    registry.register_tool("AIForgeSearchTool", AIForgeSearchTool)
    registry.register_tool("ReadTemplateTool", ReadTemplateTool)
    return registry


def get_platform_adapter(platform_name: str):
    workflow = UnifiedContentWorkflow()
    return workflow.platform_adapters.get(platform_name)


def setup_aiwritex():
    initialize_global_tools()
    return UnifiedContentWorkflow()
