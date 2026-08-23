# eSim Environment Manager (ESEM)

Automated EDA Tool and Dependency Management for eSim workflows.

## Problem Statement & Motivation
eSim integrates multiple external Electronic Design Automation (EDA) tools and libraries (such as KiCad, Ngspice, Python, and Git). Managing these dependencies manually across different developer and student environments frequently causes version mismatches, command path misconfigurations, and compatibility issues. This tool aims to automate detection, version auditing, and installation mapping, simplifying environment configuration for eSim users.

## Solution
The **eSim Environment Manager (ESEM)** automatically scans the host system, detects installed EDA tools, checks their versions against minimum requirements, computes a system readiness score, and provides a professional PySide6 GUI as well as a command-line interface (CLI) to scan, check updates, and confirm installations/upgrades using system package managers safely.

---

## Features
- **Real-Time Environment Detection**: Queries actual system binaries via non-blocking sub-processes with timeouts.
- **Dependency Audit & Version Comparison**: Performs semantic/numeric comparisons and flags outdated tools.
- **Ready Score & Dashboard Indicator**: Evaluates overall system readiness using a deduction-based scoring system (0-100).
- **Interactive Safe Installer/Updater**: Construct commands dynamically and confirm installs via platform package managers (`winget` on Windows, `apt` on Linux, `brew` on macOS) without automatic execution hazards.
- **Audit Trails**: Generates a standard log file (`logs/esim_manager.log`) featuring custom `SUCCESS` level tracking.
- **Dual-Interface Execution**: Comprehensive CLI options along with a responsive GUI utilizing background worker threads.

---

## System Architecture

ESEM uses a modular layered architecture to decouple presentation, application orchestration, core business logic, and configuration.

```
+-----------------------------------------------------------+
|                     Presentation Layer                    |
|                (src/gui/main_window.py, app.py)           |
+-----------------------------+-----------------------------+
                              |
                              v
+-----------------------------------------------------------+
|                     Orchestration Layer                   |
|                (src/core/environment_manager.py)          |
+-----------------------------+-----------------------------+
                              |
       +----------------------+----------------------+
       |                      |                      |
       v                      v                      v
+--------------+       +--------------+       +--------------+
| ToolDetector |       | VersionCheck |       | DepChecker   |
| (tool_det..) |       | (version_..) |       | (dep_ch..)   |
+--------------+       +--------------+       +--------------+
       |                      |                      |
       +----------------------+----------------------+
                              |
                              v
+-----------------------------------------------------------+
|                        Core Subsystems                    |
|             (installer.py, updater.py, logger.py)         |
+-----------------------------+-----------------------------+
                              |
                              v
+-----------------------------------------------------------+
|                     Configuration Layer                   |
|                      (config/tools.json)                  |
+-----------------------------------------------------------+
```

---

## Project Structure
```text
esim-environment-manager/
├── config/
│   └── tools.json              # Tool registry configuration
├── docs/
│   ├── architecture.md         # Design documentation
│   ├── testing.md              # Test documentation
│   └── user_guide.md           # User operation guide
├── logs/
│   └── esim_manager.log        # Generated audit logs
├── screenshots/                # Application state screenshots
├── src/
│   ├── __init__.py
│   ├── main.py                 # Application CLI and GUI entry point
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config_manager.py   # Loader & Schema validator
│   │   ├── dependency_checker.py # Scoring & status logic
│   │   ├── environment_manager.py # Main coordinator
│   │   ├── installer.py        # System package installs
│   │   ├── logger.py           # Log setup
│   │   ├── tool_detector.py    # Binary detection
│   │   ├── updater.py          # Version upgrades
│   │   └── version_checker.py  # Regex parsing & comparison
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── app.py              # PySide6 application starter
│   │   └── main_window.py      # Main window interface
│   └── utils/
│       ├── __init__.py
│       └── platform_utils.py   # Host OS and package helpers
├── tests/
│   ├── __init__.py
│   ├── test_config_manager.py
│   ├── test_dependency_checker.py
│   ├── test_detector.py
│   └── test_version_checker.py
├── LICENSE                     # MIT License
├── README.md                   # Project overview
└── requirements.txt            # Package dependencies
```

---

## Supported Tools Registry
| Tool ID | Display Name | Category | Command | Min. Version | Windows Package |
|---------|--------------|----------|---------|--------------|-----------------|
| `python`| Python       | Core     | `python` / `python3` | `3.10.0` | `Python.Python.3.10` |
| `git`   | Git          | Development | `git`  | `2.0.0`      | `Git.Git`       |
| `kicad` | KiCad        | EDA      | `kicad-cli` | `6.0.0`   | `KiCad.KiCad`   |
| `ngspice`| Ngspice     | Simulation | `ngspice` | `30.0`    | `Ngspice.Ngspice` |

---

## Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/esim-environment-manager/esim-environment-manager.git
   cd esim-environment-manager
   ```

2. **Set up a Virtual Environment**:
   ```bash
   python -m venv .venv
   ```

3. **Activate the Environment**:
   * **Windows**:
     ```powershell
     .venv\Scripts\activate
     ```
   * **Linux/macOS**:
     ```bash
     source .venv/bin/activate
     ```

4. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## Running the Application

ESEM supports both GUI and CLI operation modes.

### CLI Commands
- **Launch Graphical Interface (Default)**:
  ```bash
  python -m src.main
  ```
- **Scan Environment and print status report**:
  ```bash
  python -m src.main --scan
  ```
- **Verify Readiness Check and exit with status code**:
  ```bash
  python -m src.main --check
  ```
- **Show Application Version**:
  ```bash
  python -m src.main --version
  ```
- **Specify Custom Configuration File**:
  ```bash
  python -m src.main --config config/tools.json
  ```

---

## Testing

ESEM unit tests run inside an isolated mock environment.
To execute tests, run:
```bash
pytest -v
```

---

## Example Workflow (GUI)
1. **Launch**: Open the application via `python -m src.main`.
2. **Scan**: Click **SCAN ENVIRONMENT**. ESEM will check for tools and report versions.
3. **Audit**: Review the Environment Score (e.g. 90/100) and Readiness status (e.g. READY).
4. **Check Updates**: Select `Git` from the list and click **CHECK UPDATES** to query latest package manager details.
5. **Install / Upgrade**: Click **INSTALL** on any missing tool (like `KiCad`). A confirmation modal displays the package manager command to execute before launching the subprocess.
6. **Troubleshooting**: Inspect the live console logging panel at the bottom or reference `logs/esim_manager.log`.

---

## Limitations & Future Work
- **Package Manager Dependability**: Windows installations rely on `winget`. If `winget` is blocked by enterprise rules or missing, installation fallback is manual.
- **Sudo Privilege**: Linux installs (`apt-get`) require password validation. Future updates will leverage Polkit/pkexec prompts.
- **eSim Profile Integration**: Future extensions will support importing specific compiler toolchain JSON configurations dynamically.

## License
Distributed under the MIT License. See `LICENSE` for details.