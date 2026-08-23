import json
import os
from typing import Dict, Any, List

class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    pass

class ConfigManager:
    # Essential fields required for any tool entry
    REQUIRED_FIELDS = {
        "id",
        "display_name",
        "category",
        "command",
        "minimum_version",
    }

    def __init__(self, config_path: str = None):
        if config_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_path = os.path.join(base_dir, "config", "tools.json")
        self.config_path = config_path
        self._raw_data = None
        self._profiles = {}

    def load_raw(self) -> Dict[str, Any]:
        """Loads raw JSON configuration dictionary."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found at: {self.config_path}")

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigValidationError(f"Invalid JSON format in tools configuration: {e}")

        if not isinstance(data, dict):
            raise ConfigValidationError("Configuration root must be a JSON object.")

        self._raw_data = data
        self._profiles = data.get("profiles", {})
        return data

    def load_config(self) -> Dict[str, Dict[str, Any]]:
        """Loads and validates the tools registry configuration.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary mapping tool ID to tool details.
        """
        data = self.load_raw()

        # Handle both {"tools": [...]} list format and {"tools": {...}} dict format
        if "tools" not in data:
            raise ConfigValidationError("Configuration must contain a top-level 'tools' field.")

        raw_tools = data["tools"]
        validated_tools = {}

        if isinstance(raw_tools, list):
            for idx, tool in enumerate(raw_tools):
                if not isinstance(tool, dict):
                    raise ConfigValidationError(f"Tool at index {idx} is not a JSON object.")
                self._validate_and_store_tool(tool, idx, validated_tools)
        elif isinstance(raw_tools, dict):
            for tool_id, tool in raw_tools.items():
                if not isinstance(tool, dict):
                    raise ConfigValidationError(f"Tool '{tool_id}' is not a JSON object.")
                tool["id"] = tool.get("id", tool_id)
                self._validate_and_store_tool(tool, tool_id, validated_tools)
        else:
            raise ConfigValidationError("The 'tools' field must be a list or dictionary.")

        return validated_tools

    def _validate_and_store_tool(self, tool: Dict[str, Any], identifier: Any, target_dict: Dict[str, Dict[str, Any]]):
        missing = self.REQUIRED_FIELDS - set(tool.keys())
        if missing:
            raise ConfigValidationError(
                f"Tool '{tool.get('id', identifier)}' is missing required fields: {', '.join(missing)}"
            )

        tool_id = tool["id"]
        if not tool_id:
            raise ConfigValidationError(f"Tool entry at '{identifier}' has an empty 'id' field.")

        # Supply defaults for v2.0 fields if absent
        tool.setdefault("required", tool.get("importance") == "REQUIRED")
        tool.setdefault("importance", "REQUIRED" if tool.get("required") else "RECOMMENDED")
        tool.setdefault("version_arguments", tool.get("version_command", ["--version"]))
        tool.setdefault("install_methods", ["winget", "apt", "brew"])
        tool.setdefault("update_methods", ["winget", "apt", "brew"])

        target_dict[tool_id] = tool

    def get_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Returns the configured EDA profiles."""
        if self._raw_data is None:
            self.load_config()
        return self._profiles
