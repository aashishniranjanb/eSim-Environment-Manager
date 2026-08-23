import os
import pytest
from unittest.mock import patch, MagicMock

from src.core.tool_discovery import ToolDiscovery

def test_discovery_path_tier():
    tools_config = {
        "python": {
            "id": "python",
            "display_name": "Python",
            "command": "python",
            "executable_names": ["python.exe", "python"],
            "version_command": ["--version"]
        }
    }
    
    with patch("shutil.which", return_value="C:\\Python312\\python.exe"), \
         patch("subprocess.run") as mock_run:
        mock_proc = MagicMock()
        mock_proc.stdout = "Python 3.12.4\n"
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc
        
        disc = ToolDiscovery(tools_config)
        res = disc.discover("python", tools_config["python"])
        
        assert res["found"] is True
        assert res["source"] == "PATH"
        assert res["confidence"] == 100
        assert res["parsed_version"] == "3.12.4"

def test_discovery_known_install_path_tier():
    tools_config = {
        "kicad": {
            "id": "kicad",
            "display_name": "KiCad",
            "executable_names": ["kicad-cli.exe"],
            "windows_paths": ["C:\\Program Files\\KiCad\\9.0\\bin\\kicad-cli.exe"],
            "version_command": ["version"]
        }
    }
    
    # Path is not on PATH, but found in known_install_path
    with patch("shutil.which", return_value=None), \
         patch("os.path.isfile", return_value=True), \
         patch("subprocess.run") as mock_run:
        mock_proc = MagicMock()
        mock_proc.stdout = "9.0.2\n"
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc
        
        disc = ToolDiscovery(tools_config)
        res = disc.discover("kicad", tools_config["kicad"])
        
        assert res["found"] is True
        assert res["source"] == "known_install_path"
        assert res["confidence"] == 95
        assert res["parsed_version"] == "9.0.2"

def test_discovery_ngspice_known_path():
    tools_config = {
        "ngspice": {
            "id": "ngspice",
            "display_name": "Ngspice",
            "executable_names": ["ngspice.exe"],
            "windows_paths": ["C:\\Spice64\\bin\\ngspice.exe"],
            "version_command": ["-v"]
        }
    }
    
    with patch("shutil.which", return_value=None), \
         patch("os.path.isfile", return_value=True), \
         patch("subprocess.run") as mock_run:
        mock_proc = MagicMock()
        mock_proc.stdout = "ngspice-38\n"
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc
        
        disc = ToolDiscovery(tools_config)
        res = disc.discover("ngspice", tools_config["ngspice"])
        
        assert res["found"] is True
        assert res["source"] == "known_install_path"
        assert res["confidence"] == 95
        assert res["parsed_version"] == "38"

def test_discovery_missing_executable():
    tools_config = {
        "openroad": {
            "id": "openroad",
            "display_name": "OpenROAD",
            "executable_names": ["openroad"]
        }
    }
    
    with patch("shutil.which", return_value=None), \
         patch("os.path.isfile", return_value=False):
        disc = ToolDiscovery(tools_config)
        res = disc.discover("openroad", tools_config["openroad"])
        
        assert res["found"] is False
        assert res["source"] == "NOT_FOUND"
        assert res["confidence"] == 0
        assert res["status"] == "MISSING"

def test_discovery_custom_path_tier():
    tools_config = {
        "yosys": {
            "id": "yosys",
            "display_name": "Yosys",
            "custom_paths": ["C:\\custom\\yosys.exe"]
        }
    }
    
    with patch("shutil.which", return_value=None), \
         patch("os.path.isfile", return_value=True), \
         patch("os.access", return_value=True), \
         patch("subprocess.run") as mock_run:
        mock_proc = MagicMock()
        mock_proc.stdout = "Yosys 0.38"
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc
        
        disc = ToolDiscovery(tools_config)
        res = disc.discover("yosys", tools_config["yosys"])
        
        assert res["found"] is True
        assert res["source"] == "user_configured"
        assert res["confidence"] == 100
        assert res["parsed_version"] == "0.38"

