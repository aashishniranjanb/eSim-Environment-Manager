import logging
from typing import Dict, Any

from src.core.tool_discovery import ToolDiscovery
from src.core.logger import ActionLogger

class ToolDetector:
    """Facade for tool detection wrapping ToolDiscovery."""
    def __init__(self, tools_config: Dict[str, Dict[str, Any]]):
        self.tools = tools_config
        self.discovery = ToolDiscovery(tools_config)
        self.logger = ActionLogger.get_logger()

    def detect_tool(self, tool_id: str) -> Dict[str, Any]:
        """Detects a single tool by ID using the discovery pipeline."""
        if tool_id not in self.tools:
            raise KeyError(f"Tool '{tool_id}' not found in tools configuration.")
        return self.discovery.discover(tool_id, self.tools[tool_id])

    def scan(self) -> Dict[str, Dict[str, Any]]:
        """Scans the host system for all configured tools."""
        return self.discovery.discover_all(self.tools)
