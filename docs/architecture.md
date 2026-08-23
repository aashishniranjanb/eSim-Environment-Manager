# Architecture Specification - ESEM

This document provides a technical specification of the design and architecture of the **eSim Environment Manager (ESEM)**.

---

## 1. System Overview
ESEM is designed as a modular, layered desktop and CLI utility built in Python 3.10+ and PySide6. The main objective is to detect, audit, install, and upgrade external EDA dependencies (Python, Git, KiCad, Ngspice) required for the FOSSEE eSim Semester Long Internship.

---

## 2. Layered Architecture
ESEM is organized into four main architectural layers:

```
+-----------------------------------------------------------+
| Presentation Layer (PySide6 GUI, CLI Parser)             |
+-----------------------------+-----------------------------+
                              |
                              v
+-----------------------------------------------------------+
| Orchestration / Application Layer (EnvironmentManager)     |
+-----------------------------+-----------------------------+
                              |
                              v
+-----------------------------------------------------------+
| Core Logic Layer (Detector, Version/Dependency Checkers)   |
+-----------------------------+-----------------------------+
                              |
                              v
+-----------------------------------------------------------+
| Infrastructure & Configuration Layer (Registry JSON, Logs)|
+-----------------------------------------------------------+
```

### 2.1 Presentation Layer
- **`src/gui/main_window.py`**: The GUI MainWindow implemented in PySide6. Uses a dashboard format showing overall score, readiness status, tool detail table, interactive action buttons, and live log console. It leverages `ActionWorker` (subclassed from `QThread`) to run time-consuming OS operations asynchronously without blocking the UI main loop.
- **`src/gui/app.py`**: Simple loader that instantiates `QApplication` and executes the MainWindow.
- **`src/main.py`**: Command Line Interface entry point. Parses command line parameters (`--scan`, `--check`, `--version`, `--config`) and delegates processing to the orchestration layer or launches the GUI.

### 2.2 Orchestration Layer
- **`src/core/environment_manager.py`**: Acts as a Facade and central coordinator. Directs core services (detector, version checker, dependency checker, installer, updater) and caches scanned state, dependency evaluation, scores, and readiness results. It offers a clean public API for presentation layers.

### 2.3 Core Logic Layer
- **`src/core/tool_detector.py`**: Determines if the tools configured in `tools.json` are installed on the host. Locates binaries using `shutil.which` and executes version checks with `subprocess.run` (with a default 5-second timeout and `shell=False` for security).
- **`src/core/version_checker.py`**: Utility to parse version strings using regex filters and perform numeric semantic component comparisons.
- **`src/core/dependency_checker.py`**: Checks if the scanned system versions satisfy configured requirements. Computes a system score based on deductions:
  - Required tool missing: -25
  - Required tool outdated: -15
  - Optional tool missing: -5
  - Unknown/Error status: -5
- **`src/core/installer.py`**: Safe wrapper for building and executing package installation commands using platform-native managers (`winget`, `apt-get`, `brew`).
- **`src/core/updater.py`**: Safe wrapper for checking update status and executing upgrades.

### 2.4 Infrastructure & Configuration Layer
- **`config/tools.json`**: Registry holding tool categories, execution configurations, versioning parameters, package names, and installation criteria.
- **`src/core/config_manager.py`**: Reads and validates the config JSON against structural schemas.
- **`src/core/logger.py`**: Tailors log format output (`YYYY-MM-DD HH:MM:SS | LEVEL | Message`) and registers a custom `SUCCESS` logging level for auditing.
- **`src/utils/platform_utils.py`**: Identifies the host system and verifies the presence of native package managers.

---

## 3. Key Process Flows

### 3.1 Tool Scanning Flow
```
[GUI/CLI User Action] 
       |
       v
EnvironmentManager.scan_environment()
       |
       +---> 1. ConfigManager.load_config() (Resolves schema and platform commands)
       +---> 2. ToolDetector.scan()
       |         |
       |         +---> shutil.which(cmd) -> If exists, run "cmd version_arg" (timeout=5s)
       |         +---> VersionChecker.extract_version(raw_output)
       |
       +---> 3. DependencyChecker.check() (Calculates status code: READY, MISSING, OUTDATED, etc.)
       +---> 4. DependencyChecker.calculate_score() (Calculates readiness status and score)
       |
       v
[Update GUI/CLI View]
```

### 3.2 Installation Flow
1. User selects a tool that is not installed in the GUI.
2. User clicks **INSTALL**.
3. `Installer.build_install_command(tool)` retrieves the package name and constructs the platform package manager command list.
4. GUI prompts the user with a confirmation dialog displaying the exact command line (e.g. `winget install --id KiCad.KiCad --exact --interactive`).
5. Upon approval, GUI starts `ActionWorker(QThread)` executing `EnvironmentManager.install_tool(tool_id)`.
6. Subprocess runs with a 10-minute timeout. Outputs are captured and logged to the panel/file.
7. Upon execution finish, `EnvironmentManager.scan_environment()` is triggered automatically to verify if installation was successful.
8. GUI updates table and readiness dashboard.

---

## 4. Error Handling & Robustness
- **Process Isolation**: All external executions run through `subprocess.run` with list parameters and `shell=False`. This eliminates shell injection vulnerabilities.
- **Timeouts**: Process executions have rigid timeouts (5 seconds for detection, 10 minutes for package manager installation/upgrades) to prevent the application from hanging.
- **Graceful Failures**: Standard OS permissions, missing paths, and timeout exceptions are caught explicitly in the detector and written to logs. The application marks the corresponding tool with status `"ERROR"` or `"UNKNOWN"` instead of crashing.

