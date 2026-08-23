import json
import os
from typing import Dict, Any, List

class ConfigValidationError(Exception):
    """Raised when the configuration validation fails."""
    pass

class ConfigManager:
    REQUIRED_FIELDS = {
        "id",
        "display_name",
        "category",
        "command",
        "version_arguments",
        "required",
        "minimum_version",
        "install_methods",
        "update_methods"
    }

    def __init__(self, config_path: str = None):
        if config_path is None:
            # Default to config/tools.json at the project root
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_path = os.path.join(base_dir, "config", "tools.json")
        self.config_path = config_path

    def load_config(self) -> Dict[str, Dict[str, Any]]:
        """Loads and validates the tools registry configuration.
        
        Returns:
            Dict[str, Dict[str, Any]]: A dictionary mapping tool ID to tool details.
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found at: {self.config_path}")

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigValidationError(f"Invalid JSON format in tools configuration: {e}")

        if not isinstance(data, dict) or "tools" not in data:
            raise ConfigValidationError("Configuration must contain a top-level 'tools' list/dictionary.")

        tools_list = data["tools"]
        if not isinstance(tools_list, list):
            raise ConfigValidationError("The 'tools' field in configuration must be a list.")

        validated_tools = {}
        for idx, tool in enumerate(tools_list):
            if not isinstance(tool, dict):
                raise ConfigValidationError(f"Tool at index {idx} is not a valid JSON object.")
            
            # Validate required fields
            missing_fields = self.REQUIRED_FIELDS - set(tool.keys())
            if missing_fields:
                raise ConfigValidationError(
                    f"Tool at index {idx} (ID: {tool.get('id', 'unknown')}) is missing required fields: {', '.join(missing_fields)}"
                )
            
            tool_id = tool["id"]
            if not tool_id:
                raise ConfigValidationError(f"Tool at index {idx} has an empty 'id' field.")
            
            validated_tools[tool_id] = tool

        return validated_tools

