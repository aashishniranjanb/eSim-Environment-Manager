import pytest
import os
import json
import tempfile
from src.core.config_manager import ConfigManager, ConfigValidationError

def test_load_valid_config():
    valid_data = {
        "tools": [
            {
                "id": "test_tool",
                "display_name": "Test Tool",
                "category": "Testing",
                "command": "test-cmd",
                "version_arguments": ["--version"],
                "required": True,
                "minimum_version": "1.0.0",
                "install_methods": ["winget"],
                "update_methods": ["winget"]
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json", encoding="utf-8") as f:
        json.dump(valid_data, f)
        temp_path = f.name
        
    try:
        manager = ConfigManager(temp_path)
        config = manager.load_config()
        assert "test_tool" in config
        assert config["test_tool"]["display_name"] == "Test Tool"
        assert config["test_tool"]["required"] is True
    finally:
        os.remove(temp_path)

def test_reject_invalid_config():
    # Not a dictionary config
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json", encoding="utf-8") as f:
        json.dump(["not", "a", "dict"], f)
        temp_path = f.name
    try:
        manager = ConfigManager(temp_path)
        with pytest.raises(ConfigValidationError):
            manager.load_config()
    finally:
        os.remove(temp_path)

    # Missing tools key
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json", encoding="utf-8") as f:
        json.dump({"wrong_key": []}, f)
        temp_path = f.name
    try:
        manager = ConfigManager(temp_path)
        with pytest.raises(ConfigValidationError):
            manager.load_config()
    finally:
        os.remove(temp_path)

def test_missing_required_field():
    # Missing minimum_version
    invalid_data = {
        "tools": [
            {
                "id": "test_tool",
                "display_name": "Test Tool",
                "category": "Testing",
                "command": "test-cmd",
                "version_arguments": ["--version"],
                "required": True,
                # "minimum_version" is missing!
                "install_methods": ["winget"],
                "update_methods": ["winget"]
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json", encoding="utf-8") as f:
        json.dump(invalid_data, f)
        temp_path = f.name
        
    try:
        manager = ConfigManager(temp_path)
        with pytest.raises(ConfigValidationError) as exc_info:
            manager.load_config()
        assert "minimum_version" in str(exc_info.value)
    finally:
        os.remove(temp_path)

