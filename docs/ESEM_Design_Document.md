# eSim Environment Manager (ESEM)
## System Design & Architectural Specification Document

**Project**: Automated Tool & Environment Manager for eSim  
**Screening Task**: FOSSEE eSim Semester Long Internship Autumn 2026 (Task 5)  
**Version**: 2.0.0 Production  

---

## 1. Executive Summary & Candidate Information

The **eSim Environment Manager (ESEM v2.0.0)** is an open-source, cross-platform environment management and dependency intelligence platform designed specifically for eSim and the broader open-source Electronic Design Automation (EDA) ecosystem. 

ESEM replaces ad-hoc environment setup with a 5-tier discovery pipeline, semantic version auditing, category-weighted health scoring, EDA workflow profile analysis, non-blocking PySide6 GUI dashboard, and a package-manager abstraction layer for safe, user-confirmed software installation and upgrades.

---

## 2. Problem Statement

eSim is an open-source EDA tool for circuit design, simulation, analysis, and PCB layout. It integrates multiple independent open-source software tools and libraries, including:
- **KiCad** (Schematic capture and PCB layout)
- **Ngspice** (SPICE circuit simulation)
- **Python** (Core scripting, execution, and GUI engine)
- **Git** (Version control and repository management)
- **Digital Synthesis & HDL Tools** (Yosys, Verilator, Icarus Verilog, GHDL)

### Core Challenges:
1. **PATH Dependency Vulnerabilities**: Traditional discovery relies on `shutil.which` or environment `PATH`. On Windows, tools like KiCad or Ngspice are frequently installed in standard program directories (`C:\Program Files\KiCad\9.0\bin\kicad-cli.exe`, `C:\Spice64\bin\ngspice.exe`) without being added to the system `PATH`. Simple `which` checks report these tools as missing.
2. **Version Mismatches**: Incompatible versions of KiCad or Ngspice break simulation parameter passing or file formats.
3. **Opaque Readiness Indicators**: Students and researchers lack clear feedback on whether their machine is equipped for specific tasks (e.g. PCB design vs RTL synthesis vs eSim simulation).
4. **Dangerous Auto-Installers**: Automated installer scripts that invoke shell commands without confirmation risk damaging host system packages or failing silently.

---

## 3. Objectives & Official Task 5 Requirements Mapping

ESEM was built to fulfill all official requirements of FOSSEE eSim Task 5:

| Requirement ID | Official Requirement Title | ESEM v2.0.0 Implementation Evidence |
|---|---|---|
| **Req 1** | **Tool Installation Management** | `installer.py`, `package_manager` abstraction (`winget`, `apt`, `brew`), modal preview confirmations, zero `shell=True` risk. |
| **Req 2** | **Update and Upgrade System** | `updater.py`, package update querying, candidate version preview, confirmation modals. |
| **Req 3** | **Configuration Handling** | `config/tools.json`, `config_manager.py`, dynamic schema v2.0 validation, custom search paths. |
| **Req 4** | **Dependency Checker** | `dependency_checker.py`, `profile_analyzer.py`, category-weighted health score (0-100), transparent deduction reasons. |
| **Req 5** | **User Interface** | PySide6 Royal Engineering Console (`main_window.py`) featuring Dashboard, Tool Inventory, Profiles, Inspector, and Logs. |
| **Req 6** | **Action Logging** | `logger.py`, structured logs with `SUCCESS` level saved to `logs/esim_manager.log`. |
| **Req 7** | **Cross-Platform Support** | `platform_utils.py` and `tool_discovery.py` multi-OS discovery for Windows, Linux, and macOS. |

---

## 4. System Architecture & Module Breakdown

ESEM follows a strict **Modular Layered Architecture**:

```text
+-----------------------------------------------------------------------+
|                         Presentation Layer                            |
|             PySide6 GUI (main_window.py) / CLI (main.py)              |
+-----------------------------------+-----------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|                    Application Orchestration Layer                    |
|                      (core/environment_manager.py)                    |
+-----------------------------------+-----------------------------------+
                                    |
            +-----------------------+-----------------------+
            |                       |                       |
            v                       v                       v
+-----------------------+ +-------------------+ +-----------------------+
| 5-Tier Discovery      | | Dependency &      | | EDA Profile           |
| Pipeline              | | Health Scoring    | | Analyzer              |
| (tool_discovery.py)   | | (dep_checker.py)  | | (profile_analyzer.py)|
+-----------------------+ +-------------------+ +-----------------------+
            |                       |                       |
            +-----------------------+-----------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|                   Infrastructure & Services Layer                     |
|  ConfigManager (config_manager.py)  |  VersionChecker (ver_checker.py)|
|  Installer (installer.py)           |  Updater (updater.py)           |
|  Logger (logger.py)                 |  PlatformUtils (platform_utils)|
+-----------------------------------+-----------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|                           Host OS Binaries                            |
|             (Windows Program Files / Linux / macOS Paths)             |
+-----------------------------------------------------------------------+
```

---

## 5. 5-Tier Tool Discovery Algorithm

To solve detection failures on Windows, ESEM implements a 5-tier discovery algorithm in `src/core/tool_discovery.py`:

```text
  [Start Discovery for Tool]
             |
             v
   +-------------------+      Yes
   | 1. PATH Lookup    | ------------> [Record Location | Conf: 100%]
   +-------------------+
             | No
             v
   +-------------------+      Yes
   | 2. Custom Paths   | ------------> [Record Location | Conf: 100%]
   +-------------------+
             | No
             v
   +-------------------+      Yes
   | 3. Known Globs    | ------------> [Record Location | Conf: 95%]
   | (Program Files)   |
   +-------------------+
             | No
             v
   +-------------------+      Yes
   | 4. Platform Search| ------------> [Record Location | Conf: 90%]
   +-------------------+
             | No
             v
   [Status: NOT_FOUND | Conf: 0%]
```

### Version Query Protocol:
Once a binary path is resolved, ESEM probes candidate version flags (`kicad-cli version`, `--version`, `-v`, `-V`) with a 5-second timeout.
- If version parsed: Status = `DETECTED` / `READY`.
- If binary exists but version output string is unparseable: Status = `VERSION_UNKNOWN` (binary location & confidence preserved).
- If binary missing: Status = `MISSING` or `OPTIONAL`.

---

## 6. Configuration Architecture (`config/tools.json`)

The entire tool ecosystem is defined externally in `config/tools.json` (Schema v2.0):

```json
{
  "metadata": { "schema_version": "2.0" },
  "profiles": {
    "eSim_basic": {
      "name": "eSim Core Workflow",
      "required": ["python", "git"],
      "recommended": ["kicad", "ngspice"]
    }
  },
  "tools": [
    {
      "id": "kicad",
      "display_name": "KiCad",
      "category": "PCB",
      "importance": "RECOMMENDED",
      "command": "kicad-cli",
      "executable_names": ["kicad-cli.exe", "kicad.exe", "kicad-cli"],
      "minimum_version": "6.0.0",
      "version_command": ["version"],
      "windows_paths": [
        "%ProgramFiles%\\KiCad\\*\\bin\\kicad-cli.exe",
        "%ProgramFiles%\\KiCad\\*\\bin\\kicad.exe"
      ]
    }
  ]
}
```

`ConfigManager` parses and validates this schema at runtime, enabling users to add new open-source EDA tools without modifying Python code.

---

## 7. EDA Workflow Profiles & Intelligence

Rather than presenting an unweighted count, ESEM evaluates readiness against 4 specialized workflow profiles:
1. **eSim Core Workflow (`eSim_basic`)**: Validates Python, Git, KiCad, and Ngspice.
2. **Digital Design & RTL (`digital_design`)**: Validates Yosys, Icarus Verilog, Verilator, and GHDL.
3. **PCB Design & Fabrication (`pcb_design`)**: Validates KiCad layout toolchains.
4. **Open-Source ASIC / VLSI Flow (`open_source_vlsi`)**: Validates Yosys, OpenROAD, Magic, and Netgen.

### Category-Weighted Health Scoring:
Score budget is divided deterministically:
- **Core Required Tools**: 40 points
- **Recommended Tools**: 30 points
- **Optional Tools**: 30 points

Every point deduction generates a human-readable explanation (e.g. `"Recommended tool 'Ngspice' is not installed (-5 pts)"`).

---

## 8. Safe Package Manager Engine (`installer.py`, `updater.py`)

ESEM abstracts native package managers (`winget` on Windows, `apt-get` on Linux, `brew` on macOS):
1. User selects missing/outdated tool and clicks **INSTALL** or **UPGRADE**.
2. ESEM constructs argument lists (e.g., `["winget", "install", "--id", "KiCad.KiCad", "--exact", "--interactive"]`).
3. Modal dialog displays the exact command preview to the user.
4. Upon user confirmation, `ActionWorker` (`QThread`) executes the subprocess with `shell=False`.
5. Outputs are logged and ESEM automatically rescans the environment.

---

## 9. Royal Engineering Console GUI Layout

Built using PySide6 with a classic engineering palette (`#F5F2EA` warm cream background, `#14213D` navy primary, `#B08D57` gold accent):

```text
+-----------------------------------------------------------------------------------+
| eSim Environment Manager v2.0.0        [OS: Windows] [Last Scan: 22:01] [READY]  |
+-------------------+---------------------------------------------------------------+
| NAVIGATION        | DASHBOARD VIEW                                                |
|                   | +------------------+ +------------------+ +-----------------+ |
| [x] Dashboard     | | HEALTH SCORE     | | TOOL INVENTORY   | | PACKAGE MANAGER | |
| [ ] Tool Inventory| |  62 / 100        | | 7 / 14 Installed| | winget: Found   | |
| [ ] EDA Profiles  | +------------------+ +------------------+ +-----------------+ |
| [ ] Dependencies  |                                                               |
| [ ] Install/Update| TOOL INVENTORY TABLE                                          |
| [ ] Activity Log  | Tool       Category   Version   Status    Source              |
|                   | KiCad      PCB        9.0.7     READY     known_install_path  |
|                   | Python     Core       3.14.0    READY     PATH                |
|                   | Yosys      Digital    -         UNKNOWN   known_install_path  |
+-------------------+---------------------------------------------------------------+
```

---

## 10. Testing Strategy & Evidence

ESEM includes 26 unit and integration test cases in `tests/`:

```text
tests/test_config_manager.py::test_load_valid_config PASSED              [  3%]
tests/test_config_manager.py::test_reject_invalid_config PASSED          [  7%]
tests/test_config_manager.py::test_missing_required_field PASSED         [ 11%]
tests/test_dependency_checker.py::test_dependency_states PASSED          [ 15%]
tests/test_dependency_checker.py::test_environment_score_calculation PASSED [ 19%]
tests/test_detector.py::test_detect_python_success PASSED                [ 23%]
tests/test_detector.py::test_detect_git_success PASSED                   [ 26%]
tests/test_detector.py::test_detect_missing_executable PASSED            [ 30%]
tests/test_detector.py::test_detect_failed_version_command PASSED        [ 34%]
tests/test_discovery.py::test_discovery_path_tier PASSED                 [ 38%]
tests/test_discovery.py::test_discovery_known_install_path_tier PASSED   [ 42%]
tests/test_discovery.py::test_discovery_ngspice_known_path PASSED        [ 46%]
tests/test_discovery.py::test_discovery_missing_executable PASSED        [ 50%]
tests/test_discovery.py::test_discovery_custom_path_tier PASSED          [ 53%]
tests/test_installer_updater.py::test_installer_build_command_windows PASSED [ 57%]
tests/test_installer_updater.py::test_installer_build_command_unsupported PASSED [ 61%]
tests/test_installer_updater.py::test_updater_build_upgrade_command_windows PASSED [ 65%]
tests/test_installer_updater.py::test_updater_check_update_available_windows PASSED [ 69%]
tests/test_integration.py::test_real_machine_scan_integration PASSED     [ 73%]
tests/test_profiles.py::test_profile_esim_basic_evaluation PASSED        [ 76%]
tests/test_profiles.py::test_profile_digital_design_evaluation PASSED    [ 80%]
tests/test_profiles.py::test_profile_pcb_design_evaluation PASSED        [ 84%]
tests/test_profiles.py::test_profile_all_evaluations PASSED              [ 88%]
tests/test_version_checker.py::test_extract_version PASSED               [ 92%]
tests/test_version_checker.py::test_compare_versions PASSED              [ 96%]
tests/test_version_checker.py::test_is_compatible PASSED                 [100%]

============================= 26 passed in 1.23s ==============================
```

---

## 11. Empirical Real Machine Discovery Validation

Real machine discovery scan performed on Windows host machine confirmed:
- **KiCad 9.0.7** detected via `known_install_path` at `C:\Program Files\KiCad\9.0\bin\kicad-cli.exe` (95% confidence).
- **Python 3.14.0** detected via `PATH` at `C:\Python314\python.exe` (100% confidence).
- **Git 2.49.0** detected via `PATH` at `C:\Program Files\Git\cmd\git.exe` (100% confidence).
- **Icarus Verilog 12.0** detected via `known_install_path` at `C:\iverilog\bin\iverilog.exe` (95% confidence).
- **SymbiYosys 0.66** detected via `known_install_path` at `C:\oss-cad-suite\bin\sby.exe` (95% confidence).

---

## 12. Limitations & Future Work

### Limitations:
1. **Custom Binary Flags**: Tools that do not support `--version`, `version`, or `-v` output strings display status `VERSION_UNKNOWN`.
2. **Linux Sudo Prompts**: Package operations using `apt-get` require root credentials.

### Future Work:
- Polkit GTK/Qt elevation integration for Linux.
- Interactive dependency graph visualization.
- One-click workflow profile remediation.

