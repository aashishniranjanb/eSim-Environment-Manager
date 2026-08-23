import pytest
from unittest.mock import patch, MagicMock
from src.core.installer import Installer
from src.core.updater import Updater

def test_installer_build_command_windows():
    tool = {
        "id": "git",
        "install_methods": ["winget"],
        "packages": {"windows": "Git.Git"}
    }
    
    with patch("src.core.installer.detect_platform", return_value="windows"), \
         patch("shutil.which", return_value="C:\\Windows\\System32\\winget.exe"):
        installer = Installer()
        cmd = installer.build_install_command(tool)
        
        assert cmd == ["winget", "install", "--id", "Git.Git", "--exact", "--interactive"]

def test_installer_build_command_unsupported():
    tool = {
        "id": "custom",
        "install_methods": ["apt"],
        "packages": {"linux": "custom-pkg"}
    }
    
    with patch("src.core.installer.detect_platform", return_value="windows"):
        installer = Installer()
        cmd = installer.build_install_command(tool)
        
        assert cmd is None

def test_updater_build_upgrade_command_windows():
    tool = {
        "id": "kicad",
        "update_methods": ["winget"],
        "packages": {"windows": "KiCad.KiCad"}
    }
    
    with patch("src.core.updater.detect_platform", return_value="windows"), \
         patch("shutil.which", return_value="C:\\Windows\\System32\\winget.exe"):
        updater = Updater()
        cmd = updater.build_upgrade_command(tool)
        
        assert cmd == ["winget", "upgrade", "--id", "KiCad.KiCad", "--exact", "--interactive"]

def test_updater_check_update_available_windows():
    tool = {
        "id": "git",
        "packages": {"windows": "Git.Git"}
    }
    
    with patch("src.core.updater.detect_platform", return_value="windows"), \
         patch("shutil.which", return_value="C:\\Windows\\System32\\winget.exe"), \
         patch("subprocess.run") as mock_run:
        mock_proc = MagicMock()
        mock_proc.stdout = "Git.Git  Git  2.40.0  2.45.2  winget\n"
        mock_run.return_value = mock_proc
        
        updater = Updater()
        has_update = updater.check_update_available(tool)
        
        assert has_update is True

