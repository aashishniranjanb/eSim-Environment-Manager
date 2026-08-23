# ESEM User Guide

This guide describes how to use the **eSim Environment Manager (ESEM)** to audit and configure your EDA tools environment.

---

## 1. Installation & Launching

1. Open your terminal or powershell and navigate to the project directory:
   ```bash
   cd esim-environment-manager
   ```
2. Activate your virtual environment:
   * **Windows**: `.venv\Scripts\activate`
   * **Linux/macOS**: `source .venv/bin/activate`
3. Launch the desktop GUI application:
   ```bash
   python -m src.main
   ```

---

## 2. Scanning the Environment
When the application opens, it displays an empty state.
1. Click the **SCAN ENVIRONMENT** or **REFRESH** button.
2. ESEM will check system paths for all configured tools (Python, Git, KiCad, Ngspice).
3. The table will populate with the results.
4. The dashboard cards will show:
   - **Environment Score**: A rating from 0 to 100 representing how complete the setup is.
   - **Overview Stats**: The number of installed and missing tools.
   - **Readiness Badge** (top right): Color-coded overall readiness status (`READY` in green, `MOSTLY READY` in orange, or `NOT READY` in red).

---

## 3. Reading Tool Status Codes
The "Dependency Status" column in the table displays one of the following:
- **READY**: The tool is installed and its version satisfies the minimum requirements.
- **OPTIONAL**: The tool is optional (like KiCad or Ngspice) and is not installed. This does not prevent eSim from functioning but limits features.
- **MISSING**: A required tool (like Git) is missing.
- **OUTDATED**: The tool is installed but its version is older than required.
- **UNKNOWN**: The tool is installed but the version command did not return a valid semantic number.
- **ERROR**: An error occurred when running the detection process (such as permission denied).

---

## 4. Checking for Updates
1. Select an installed tool in the main table by clicking its row.
2. Click **CHECK UPDATES**.
3. ESEM will query your system's package manager in the background to verify if a newer version is available.
4. A popup dialog will inform you if an upgrade candidate exists.

---

## 5. Installing or Upgrading a Tool
ESEM integrates package managers (`winget` on Windows, `apt-get` on Linux, `brew` on macOS) to install or upgrade dependencies safely:

1. Click on a missing tool row (to install) or an outdated tool row (to upgrade).
2. Click **INSTALL** or **UPGRADE**.
3. A confirmation modal will appear, displaying the exact command that ESEM is about to run.
4. Verify the command and click **Yes** to proceed.
5. The installation will run in a background thread. You can monitor progress through the **Live Action Log** panel at the bottom.
6. Once finished, ESEM automatically performs a fresh scan and updates the dashboard.

> [!WARNING]
> ESEM will never install or modify packages automatically. Every action requires explicit user authorization via the confirmation dialog.

---

## 6. Reading Logs & Troubleshooting
All application actions, warnings, and error traces are recorded:
- **Live Panel**: The scrolling panel at the bottom of the window displays real-time execution states. Click **Clear Log** to reset the view.
- **File Log**: Technical details and exception stack traces are saved to `logs/esim_manager.log`.
- **Command-Line Issues**: If the GUI fails to launch, try running a quick scan directly in the terminal to inspect issues:
  ```bash
  python -m src.main --scan
  ```

