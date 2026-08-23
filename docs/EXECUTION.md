# ESEM Evaluator Execution Guide

This step-by-step guide is intended for FOSSEE eSim Task 5 evaluators to clone, setup, test, and run the **eSim Environment Manager (ESEM v2.0.0)**.

---

## 1. Clone the Repository
Clone the private GitHub repository to your local machine:
```bash
git clone https://github.com/<your-username>/esim-environment-manager.git
cd esim-environment-manager
```

---

## 2. Create Virtual Environment
Create an isolated Python 3.10+ virtual environment:
```bash
python -m venv .venv
```

---

## 3. Activate Virtual Environment
Activate the environment according to your operating system:

* **Windows (PowerShell)**:
  ```powershell
  .venv\Scripts\activate
  ```
* **Windows (Command Prompt)**:
  ```cmd
  .venv\Scripts\activate.bat
  ```
* **Linux / macOS (Bash / Zsh)**:
  ```bash
  source .venv/bin/activate
  ```

---

## 4. Install Dependencies
Install the required packages (`PySide6` and `pytest`):
```bash
pip install -r requirements.txt
```

---

## 5. Run Automated Unit & Integration Tests
Execute the 26-test suite:
```bash
python -m pytest -v
```

**Expected Result**:
```text
============================= 26 passed in 1.23s ==============================
```

---

## 6. Run CLI Tool Discovery Scan
Execute the 5-tier discovery scan across all 14 configured EDA tools:
```bash
python -m src.main --scan
```
This prints the tool inventory, detected versions, executable paths, discovery sources, and score deduction breakdown.

---

## 7. Run EDA Workflow Profiles Evaluation
Evaluate system readiness across the 4 specialized EDA profiles (`eSim Core`, `Digital Design`, `PCB Design`, `Open VLSI`):
```bash
python -m src.main --profiles
```

---

## 8. Run CLI Readiness Check
Run the automated environment readiness check (exits with status code `0` if READY / MOSTLY READY):
```bash
python -m src.main --check
```

---

## 9. Launch the Royal Engineering Console GUI
Launch the PySide6 desktop interface:
```bash
python -m src.main
```

### Key UI Features to Explore:
1. **Dashboard View**: View Environment Health Score, Tool Inventory Summary, and Category Cards.
2. **Tool Inventory View**: Use search & filter dropdowns. Click any row to open the **Tool Detail Inspector** drawer on the right. Click **Open File Location** to launch the directory in native File Explorer.
3. **EDA Profiles View**: Inspect readiness scores and specific workflow guidance for eSim, Digital, PCB, and Open VLSI flows.
4. **Dependencies View**: Inspect transparent itemized deduction explanations for health scoring.
5. **Install / Update View**: Inspect proposed package manager commands (`winget`, `apt`, `brew`) for missing or outdated tools.
6. **Activity Log View**: Inspect real-time action logs.

---

## 10. Inspect Log Files
All actions, warnings, and system discovery milestones are logged automatically at runtime to:
```text
logs/esim_manager.log
```

