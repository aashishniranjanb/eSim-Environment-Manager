import os
import subprocess
from unittest.mock import patch, MagicMock
from src.core.tool_detector import ToolDetector

def test_detect_python_success():
    tools_config = {
        "python": {
            "id": "python",
            "display_name": "Python",
            "category": "Core",
            "command": "python",
            "version_arguments": ["--version"],
            "required": True,
            "minimum_version": "3.10.0"
        }
    }
    
    with patch("shutil.which", return_value="C:\\Python312\\python.exe"), \
         patch("subprocess.run") as mock_run:
         
        mock_proc = MagicMock()
        mock_proc.stdout = "Python 3.12.4\n"
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc
        
        detector = ToolDetector(tools_config)
        results = detector.scan()
        
        assert results["python"]["installed"] is True
        assert results["python"]["executable_path"] == "C:\\Python312\\python.exe"
        assert results["python"]["parsed_version"] == "3.12.4"
        assert results["python"]["status"] == "DETECTED"
        assert results["python"]["error"] is None

def test_detect_git_success():
    tools_config = {
        "git": {
            "id": "git",
            "display_name": "Git",
            "category": "Development",
            "command": "git",
            "version_arguments": ["--version"],
            "required": True,
            "minimum_version": "2.0.0"
        }
    }
    
    with patch("shutil.which", return_value="/usr/bin/git"), \
         patch("subprocess.run") as mock_run:
         
        mock_proc = MagicMock()
        mock_proc.stdout = "git version 2.45.2"
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc
        
        detector = ToolDetector(tools_config)
        results = detector.scan()
        
        assert results["git"]["installed"] is True
        assert results["git"]["parsed_version"] == "2.45.2"
        assert results["git"]["status"] == "DETECTED"

def test_detect_missing_executable():
    tools_config = {
        "kicad": {
            "id": "kicad",
            "display_name": "KiCad",
            "category": "EDA",
            "command": "kicad-cli",
            "version_arguments": ["--version"],
            "required": False,
            "minimum_version": "6.0.0"
        }
    }
    
    with patch("shutil.which", return_value=None), \
         patch("os.path.isfile", return_value=False):
        detector = ToolDetector(tools_config)
        results = detector.scan()
        
        assert results["kicad"]["installed"] is False
        assert results["kicad"]["executable_path"] is None
        assert results["kicad"]["parsed_version"] is None
        assert results["kicad"]["status"] == "MISSING"

def test_detect_failed_version_command():
    tools_config = {
        "git": {
            "id": "git",
            "display_name": "Git",
            "category": "Development",
            "command": "git",
            "version_arguments": ["--version"],
            "required": True,
            "minimum_version": "2.0.0"
        }
    }
    
    expected_path = os.path.abspath("/usr/bin/git")
    with patch("shutil.which", return_value="/usr/bin/git"), \
         patch("subprocess.run", side_effect=subprocess.SubprocessError("Process execution error")):
        detector = ToolDetector(tools_config)
        results = detector.scan()
        
        assert results["git"]["installed"] is True
        assert results["git"]["executable_path"] == expected_path
        assert results["git"]["parsed_version"] is None
        assert results["git"]["status"] == "VERSION_UNKNOWN"
        assert "Process execution error" in results["git"]["error"]