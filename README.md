# eSim Environment Manager (ESEM)

A cross-platform environment management and dependency intelligence tool for open-source EDA workflows.

---

## Overview

eSim depends on several external open-source EDA tools and libraries (such as KiCad, Ngspice, Python, and Git). Manually locating binaries, verifying versions, managing dependencies, and maintaining these tools across diverse user operating systems can be difficult and error-prone.

**ESEM** provides a centralized desktop and command-line interface for:
- Tool discovery across standard system directories
- Semantic version parsing and auditing
- Dependency analysis & transparent health scoring
- EDA workflow profiling (eSim, Digital RTL, PCB Design, Open VLSI)
- Installation management via OS package managers
- Update and upgrade management
- Dynamic tool registry configuration
- Auditable action logging

---

## Key Features

### 1. Robust Tool Discovery
ESEM uses a 5-tier discovery pipeline rather than relying solely on `PATH`:
1. **PATH Lookup**: Checks system `PATH` via `shutil.which`.
2. **Candidate Binary Names**: Searches for tool-specific binary variants (e.g. `kicad-cli.exe`, `kicad.exe`, `ngspice_con.exe`).
3. **Known Installation Locations**: Scans standard program directories (e.g., `C:\Program Files\KiCad\*\bin\`, `C:\Spice64\bin\`, `C:\oss-cad-suite\bin\`).
4. **Platform-Specific Search**: Resolves default installation directories on Windows, Linux, and macOS.
5. **User-Configured Custom Paths**: Allows user-specified executable locations.

### 2. Tool Inventory
Supports a registry of 14 open-source EDA, HDL, simulation, and VLSI tools:
- **Core**: Python, Git
- **PCB Design**: KiCad
- **Circuit Simulation**: Ngspice, Qucs-S
- **Digital Design & Synthesis**: Yosys, Verilator, Icarus Verilog, GHDL
- **Formal & FPGA**: SymbiYosys, nextpnr
- **Open VLSI / ASIC Flow**: OpenROAD, Magic, Netgen

### 3. EDA Workflow Profiles
Evaluates ecosystem readiness across 4 specialized profiles:
- **eSim Basic**: Python, Git, KiCad, Ngspice
- **Digital Design**: Yosys, Icarus Verilog, Verilator, GHDL
- **PCB Design**: KiCad, Python, Git
- **Open-Source VLSI**: Yosys, OpenROAD, Magic, Netgen

### 4. Dependency Analysis
Provides:
- Overall Readiness Status (`READY`, `MOSTLY READY`, `NOT READY`)
- Category-weighted Environment Health Score (Core 40, Recommended 30, Optional 30)
- Identification of missing or outdated dependencies
- Transparent itemized explanations for every score deduction

### 5. Installation and Updates
- Package-manager abstraction for supported platforms (`winget` on Windows, `apt` on Linux, `brew` on macOS).
- **Safety First**: Commands are previewed in a modal dialog before user-confirmed execution with zero `shell=True` risk.

### 6. User Interface
- Built using PySide6 styled with a classic **Royal Engineering Console** palette (`#F5F2EA` warm cream, `#14213D` navy primary, `#B08D57` gold accent).
- Includes Sidebar Navigation, Dashboard, Tool Inventory with Filter/Search, Tool Inspector Drawer (with native File Explorer launcher), EDA Profiles Inspector, and Activity Log.

### 7. Logging
All discovery runs, status audits, and package commands are logged with timestamps and custom `SUCCESS` level tracking to `logs/esim_manager.log`.

---

## Architecture

```text
                    ESEM v2.0.0
                         |
           +-------------+-------------+
           |                           |
          GUI                         CLI
    (main_window.py)               (main.py)
           |                           |
           +-------------+-------------+
                         |
                 Application Core
              (environment_manager.py)
                         |
    +--------------------+--------------------+
    |                    |                    |
Tool Discovery       Dependency         Profile Analyzer
(tool_discovery.py)  Checker            (profile_analyzer.py)
    |                (dep_checker.py)         |
    +--------------------+--------------------+
                         |
                Configuration Layer
                 (config/tools.json)
                         |
       +-----------------+-----------------+
       |                 |                 |
   Installer          Updater           Logger
  (installer.py)     (updater.py)     (logger.py)
                         |
                  Operating System
             (Windows / Linux / macOS)
```

---

## Requirements
- **Python**: 3.10 or higher
- **Git**: 2.0 or higher
- **PySide6**: 6.0+
- **pytest**: 7.0+

---

## Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd esim-environment-manager
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv .venv
   ```

3. **Activate the Virtual Environment**:
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

### Graphical User Interface (GUI)
Launch the Royal Engineering Console:
```bash
python -m src.main
```

### Command Line Interface (CLI)
- **14-Tool Discovery Scan & Report**:
  ```bash
  python -m src.main --scan
  ```
- **Environment Doctor Diagnosis**:
  ```bash
  python -m src.main --doctor
  ```
- **Export Environment Report**:
  ```bash
  python -m src.main --report environment.json
  ```
- **EDA Workflow Profiles Evaluation**:
  ```bash
  python -m src.main --profiles
  ```
- **Readiness Check & Exit Status Code**:
  ```bash
  python -m src.main --check
  ```
- **Display Version Information**:
  ```bash
  python -m src.main --version
  ```
- **Specify Custom Tools Configuration**:
  ```bash
  python -m src.main --config config/tools.json
  ```

---

## Testing

Run the automated unit and integration test suite:
```bash
python -m pytest -v
```

### Current Test Status
- **Total Test Cases**: 26 passed
- **Failures**: 0
- **Execution Time**: ~1.2 seconds
- Includes mock-based discovery isolation and real-machine scan integration tests.

---

## Project Structure
```text
esim-environment-manager/
├── config/
│   └── tools.json              # Schema v2.0 tool registry & profiles
├── docs/
│   ├── ESEM_Design_Document.md # Official submission design document
│   ├── EXECUTION.md            # Evaluator step-by-step execution guide
│   ├── architecture.md         # Architecture specification
│   ├── testing.md              # Test documentation
│   └── user_guide.md           # User operations guide
├── logs/
│   └── .gitkeep                # Runtime log directory anchor
├── src/
│   ├── __init__.py
│   ├── main.py                 # CLI argument parser & app runner
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config_manager.py   # Registry loader & schema validator
│   │   ├── dependency_checker.py # Category health scoring & deductions
│   │   ├── environment_manager.py # Application coordinator facade
│   │   ├── installer.py        # Package manager installation abstraction
│   │   ├── logger.py           # Custom logging setup
│   │   ├── profile_analyzer.py # EDA profile readiness evaluator
│   │   ├── tool_detector.py    # Detector wrapper
│   │   ├── tool_discovery.py   # 5-tier layered discovery pipeline
│   │   ├── updater.py          # Package manager upgrade abstraction
│   │   └── version_checker.py  # Regex parsing & numeric comparison
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── app.py              # Qt Application wrapper
│   │   └── main_window.py      # Royal Engineering Console UI
│   └── utils/
│       ├── __init__.py
│       └── platform_utils.py   # Host OS & package manager helpers
├── tests/
│   ├── __init__.py
│   ├── test_config_manager.py
│   ├── test_dependency_checker.py
│   ├── test_detector.py
│   ├── test_discovery.py
│   ├── test_installer_updater.py
│   ├── test_integration.py
│   ├── test_profiles.py
│   └── test_version_checker.py
├── .gitignore
├── LICENSE                     # MIT License
├── README.md                   # Submission overview
└── requirements.txt
```

---

## Design Goals
- **Modular Architecture**: Decoupled presentation, coordination, core discovery, and configuration layers.
- **Cross-Platform Discovery**: Layered pipeline resolving standard paths on Windows, Linux, and macOS.
- **Safe Package Management**: Command preview, zero `shell=True` risk, user confirmation required before any system modification.
- **Transparent Dependency Analysis**: Category-weighted scoring with itemized score deduction reasons.
- **Extensible Tool Registry**: Driver and profile configuration defined purely in JSON outside Python source code.
- **Responsive GUI**: Non-blocking `QThread` workers execute background OS commands without UI freezing.
- **Testable Components**: 100% test isolation using mock fixtures.

---

## Limitations
- **Version Flag Variation**: Some external tools do not expose a standard `--version` flag; ESEM handles these by probing fallback commands (`version`, `-v`, `-V`) or recording `VERSION_UNKNOWN`.
- **Package Manager Availability**: Automatic installation relies on `winget` (Windows), `apt-get` (Linux), or `brew` (macOS). If uninstalled, manual installation guidance is provided.
- **Sudo Authentication on Linux**: Executing `apt-get` requires elevated privileges.
- **Conservative Discovery**: Tool discovery requires binary verification and intentionally avoids recursive whole-disk searches to ensure fast execution.

---

## Future Work
- **Automated Environment Repair**: One-click remediation for missing recommended tools.
- **Expanded Package Managers**: Support for `pacman`, `dnf`, `snap`, and `flatpak`.
- **eSim-Specific Configuration Profiles**: Importing custom toolchain JSON configurations from eSim projects.
- **Dependency Graph Visualization**: Interactive graphical mapping of EDA toolchain relationships.