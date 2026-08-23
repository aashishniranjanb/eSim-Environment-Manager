# Testing Documentation - ESEM

This document outlines the testing strategy, test coverage, and execution instructions for the **eSim Environment Manager (ESEM)** test suite.

---

## 1. Test Environment
The testing suite is designed around the **`pytest`** framework and targets Python 3.10+.
- All dependencies required for testing are listed in the `requirements.txt` file (includes `pytest`).
- Unit tests run within an isolated context. They do **not** require external EDA tools (KiCad, Ngspice) to be installed on the testing host.

---

## 2. Mocking Strategy
The test suite isolates logic using standard Python unit testing mocks (`unittest.mock.patch`):
- **`shutil.which`** is mocked to simulate the presence or absence of external executable paths.
- **`subprocess.run`** is mocked to return custom mock processes containing preset `stdout`, `stderr`, and exit codes. This allows testing version string extraction on a wide range of platforms and test cases without running actual commands.
- **`tempfile.NamedTemporaryFile`** is utilized to test configuration loading, ensuring that file I/O operations are kept isolated and temporary configuration files are deleted immediately after testing.

---

## 3. Test Cases & Coverage

### 3.1 Configuration Manager (`tests/test_config_manager.py`)
- **`test_load_valid_config`**: Confirms that a well-formatted tool configuration is parsed correctly and maps attributes.
- **`test_reject_invalid_config`**: Ensures that invalid JSON or incorrect schema root nodes raise a `ConfigValidationError`.
- **`test_missing_required_field`**: Checks that omission of key schema attributes (e.g. `minimum_version`) raises a validation error explicitly naming the missing field.

### 3.2 Tool Detector (`tests/test_detector.py`)
- **`test_detect_python_success`**: Emulates a successful `python --version` command and verifies version parsing and absolute path resolution.
- **`test_detect_git_success`**: Verifies detection and semantic extraction of Git commands.
- **`test_detect_missing_executable`**: Simulates cases where `shutil.which` returns `None`, verifying that ESEM records `installed=False` and status `MISSING` gracefully.
- **`test_detect_failed_version_command`**: Evaluates system response to binary permission issues or subprocess failure, ensuring ESEM catches the exception, logs it, and sets the tool status to `ERROR`.

### 3.3 Version Checker (`tests/test_version_checker.py`)
- **`test_extract_version`**: Tests version number extraction on varying output formats (e.g. dot-separated formats like `Python 3.12.4`, single integers like `ngspice-30`).
- **`test_compare_versions`**: Verifies numeric list comparisons (newer versions, older versions, exact matches, trailing dot components).
- **`test_is_compatible`**: Checks boolean result mapping for compatible and incompatible states, as well as handling invalid version strings.

### 3.4 Dependency Checker (`tests/test_dependency_checker.py`)
- **`test_dependency_states`**: Validates status transitions:
  - Installed + satisfies version -> `READY`
  - Installed + older version -> `OUTDATED`
  - Not installed + required -> `MISSING`
  - Not installed + optional -> `OPTIONAL`
- **`test_environment_score_calculation`**: Asserts that readiness scores are calculated correctly based on configured deductions (Required missing: -25, Outdated required: -15, Optional missing: -5, Unknown/Error: -5) and map to correct readiness statuses (`READY`, `MOSTLY READY`, `NOT READY`), ensuring bounds remain strictly between 0 and 100.

---

## 4. Running Tests
To run the automated test suite, ensure the virtual environment is activated and execute:
```bash
pytest -v
```

### Expected Results
```text
tests/test_config_manager.py::test_load_valid_config PASSED
tests/test_config_manager.py::test_reject_invalid_config PASSED
tests/test_config_manager.py::test_missing_required_field PASSED
tests/test_dependency_checker.py::test_dependency_states PASSED
tests/test_dependency_checker.py::test_environment_score_calculation PASSED
tests/test_detector.py::test_detect_python_success PASSED
tests/test_detector.py::test_detect_git_success PASSED
tests/test_detector.py::test_detect_missing_executable PASSED
tests/test_detector.py::test_detect_failed_version_command PASSED
tests/test_version_checker.py::test_extract_version PASSED
tests/test_version_checker.py::test_compare_versions PASSED
tests/test_version_checker.py::test_is_compatible PASSED
```

---

## 5. Limitations
- **Virtual Environment PySide6 Mocking**: PySide6 GUI components are not mocked in unit testing; GUI integration testing must be performed manually.
- **Package Manager Execution**: Real winget, apt-get, and brew commands are not executed during tests, as it would cause mutation of host packages.

