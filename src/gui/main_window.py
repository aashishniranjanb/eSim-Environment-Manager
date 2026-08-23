import os
import sys
import logging
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QMessageBox,
    QHeaderView,
    QFrame
)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QFont, QColor

from src.core.environment_manager import EnvironmentManager
from src.utils.platform_utils import detect_platform, is_package_manager_available
from src.core.logger import ActionLogger

class ActionWorker(QThread):
    finished_signal = Signal(dict)
    
    def __init__(self, action_fn, *args, **kwargs):
        super().__init__()
        self.action_fn = action_fn
        self.args = args
        self.kwargs = kwargs
        
    def run(self):
        try:
            res = self.action_fn(*self.args, **self.kwargs)
            self.finished_signal.emit(res)
        except Exception as e:
            self.finished_signal.emit({"success": False, "output": f"Worker thread error: {e}"})

class MainWindow(QMainWindow):
    def __init__(self, config_path: str = None):
        super().__init__()
        self.setWindowTitle("eSim Environment Manager")
        self.resize(1000, 700)
        self.setMinimumSize(850, 600)
        
        # Initialize environment coordinator
        self.env_manager = EnvironmentManager(config_path)
        self.logger = ActionLogger.get_logger()
        
        self.selected_tool_id = None
        self.worker = None

        # Build UI
        self.setup_ui()
        
        # Tail logs
        self.update_log_panel("[INFO] eSim Environment Manager started. Click SCAN ENVIRONMENT to check systems.")
        
        # Enable/Disable controls initially
        self.update_button_states()

    def setup_ui(self):
        # Main central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)
        central_widget.setLayout(main_layout)
        
        # ---------------- HEADER SECTION ----------------
        header_layout = QHBoxLayout()
        
        title_desc_layout = QVBoxLayout()
        app_title = QLabel("eSim Environment Manager")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        app_title.setFont(title_font)
        
        app_desc = QLabel("Automated External EDA Tools & Environment Dependency Management for eSim Workflows")
        desc_font = QFont()
        desc_font.setPointSize(10)
        app_desc.setFont(desc_font)
        app_desc.setStyleSheet("color: #555555;")
        
        title_desc_layout.addWidget(app_title)
        title_desc_layout.addWidget(app_desc)
        header_layout.addLayout(title_desc_layout)
        
        header_layout.addStretch()
        
        # Readiness Badge
        self.readiness_badge = QLabel("NOT SCANNED")
        self.readiness_badge.setAlignment(Qt.AlignCenter)
        self.readiness_badge.setFixedWidth(160)
        self.readiness_badge.setFixedHeight(35)
        self.readiness_badge.setStyleSheet(
            "background-color: #757575; color: white; border-radius: 4px; font-weight: bold; font-size: 12px;"
        )
        header_layout.addWidget(self.readiness_badge)
        
        main_layout.addLayout(header_layout)
        
        # Divider Line
        divider1 = QFrame()
        divider1.setFrameShape(QFrame.HLine)
        divider1.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(divider1)
        
        # ---------------- DASHBOARD CARD SECTION ----------------
        dashboard_layout = QHBoxLayout()
        
        # Score Card
        self.score_card = QFrame()
        self.score_card.setFrameShape(QFrame.StyledPanel)
        self.score_card.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px;")
        score_layout = QVBoxLayout(self.score_card)
        score_title = QLabel("ENVIRONMENT SCORE")
        score_title.setAlignment(Qt.AlignCenter)
        score_title.setStyleSheet("font-size: 11px; color: #6c757d; font-weight: bold;")
        self.score_val = QLabel("N/A")
        self.score_val.setAlignment(Qt.AlignCenter)
        self.score_val.setStyleSheet("font-size: 28px; font-weight: bold; color: #212529;")
        score_layout.addWidget(score_title)
        score_layout.addWidget(self.score_val)
        
        # Status Card
        self.stats_card = QFrame()
        self.stats_card.setFrameShape(QFrame.StyledPanel)
        self.stats_card.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px;")
        stats_layout = QVBoxLayout(self.stats_card)
        stats_title = QLabel("TOOLS OVERVIEW")
        stats_title.setAlignment(Qt.AlignCenter)
        stats_title.setStyleSheet("font-size: 11px; color: #6c757d; font-weight: bold;")
        self.stats_val = QLabel("Scans Pending")
        self.stats_val.setAlignment(Qt.AlignCenter)
        self.stats_val.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057;")
        stats_layout.addWidget(stats_title)
        stats_layout.addWidget(self.stats_val)
        
        # Platform Info Card
        self.platform_card = QFrame()
        self.platform_card.setFrameShape(QFrame.StyledPanel)
        self.platform_card.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px;")
        platform_layout = QVBoxLayout(self.platform_card)
        platform_title = QLabel("PLATFORM INFO")
        platform_title.setAlignment(Qt.AlignCenter)
        platform_title.setStyleSheet("font-size: 11px; color: #6c757d; font-weight: bold;")
        
        plat = detect_platform().capitalize()
        pm = "winget" if plat == "Windows" else ("brew" if plat == "Macos" else "apt")
        pm_avail = "Available" if is_package_manager_available() else "Missing"
        self.platform_val = QLabel(f"{plat} ({pm}: {pm_avail})")
        self.platform_val.setAlignment(Qt.AlignCenter)
        self.platform_val.setStyleSheet("font-size: 13px; font-weight: bold; color: #495057;")
        platform_layout.addWidget(platform_title)
        platform_layout.addWidget(self.platform_val)
        
        dashboard_layout.addWidget(self.score_card)
        dashboard_layout.addWidget(self.stats_card)
        dashboard_layout.addWidget(self.platform_card)
        main_layout.addLayout(dashboard_layout)
        
        # ---------------- MAIN TABLE ----------------
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Tool", "Category", "Installed", "Version", "Minimum Required", "Dependency Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self.on_table_selection)
        main_layout.addWidget(self.table)
        
        # ---------------- ACTIONS BUTTONS ----------------
        actions_layout = QHBoxLayout()
        
        self.btn_scan = QPushButton("SCAN ENVIRONMENT")
        self.btn_scan.setFixedWidth(200)
        self.btn_scan.setFixedHeight(32)        
        self.btn_scan.setStyleSheet("font-weight: bold; background-color: #0d6efd; color: white;")
        self.btn_scan.clicked.connect(self.trigger_scan)
        actions_layout.addWidget(self.btn_scan)
        
        self.btn_install = QPushButton("INSTALL")
        self.btn_install.setFixedWidth(200)
        self.btn_install.setFixedHeight(32)
        self.btn_install.setStyleSheet("font-weight: bold;")
        self.btn_install.clicked.connect(self.trigger_install)
        actions_layout.addWidget(self.btn_install)
        
        self.btn_check_updates = QPushButton("CHECK UPDATES")
        self.btn_check_updates.setFixedWidth(200)
        self.btn_check_updates.setFixedHeight(32)
        self.btn_check_updates.setStyleSheet("font-weight: bold;")
        self.btn_check_updates.clicked.connect(self.trigger_check_updates)
        actions_layout.addWidget(self.btn_check_updates)
        
        self.btn_upgrade = QPushButton("UPGRADE")
        self.btn_upgrade.setFixedWidth(200)
        self.btn_upgrade.setFixedHeight(32)
        self.btn_upgrade.setStyleSheet("font-weight: bold;")
        self.btn_upgrade.clicked.connect(self.trigger_upgrade)
        actions_layout.addWidget(self.btn_upgrade)
        
        self.btn_refresh = QPushButton("REFRESH")
        self.btn_refresh.setFixedWidth(200)
        self.btn_refresh.setFixedHeight(32)
        self.btn_refresh.clicked.connect(self.trigger_scan)
        actions_layout.addWidget(self.btn_refresh)
        
        main_layout.addLayout(actions_layout)
        
        # ---------------- LOG PANEL ----------------
        log_header = QHBoxLayout()
        log_header.addWidget(QLabel("Live Action Log"))
        log_header.addStretch()
        self.btn_clear_log = QPushButton("Clear Log")
        self.btn_clear_log.clicked.connect(self.clear_log)
        log_header.addWidget(self.btn_clear_log)
        main_layout.addLayout(log_header)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFixedHeight(120)
        self.log_text.setStyleSheet("background-color: #212529; color: #f8f9fa; font-family: Consolas, monospace;")
        main_layout.addWidget(self.log_text)

    def update_log_panel(self, msg: str):
        self.log_text.append(msg)
        # Scroll to bottom
        self.log_text.ensureCursorVisible()

    def clear_log(self):
        self.log_text.clear()

    def update_button_states(self):
        """Updates buttons enabled/disabled status based on current state and selection."""
        # Disable all action buttons if a worker thread is running
        if self.worker and self.worker.isRunning():
            self.btn_scan.setEnabled(False)
            self.btn_install.setEnabled(False)
            self.btn_check_updates.setEnabled(False)
            self.btn_upgrade.setEnabled(False)
            self.btn_refresh.setEnabled(False)
            return

        self.btn_scan.setEnabled(True)
        self.btn_refresh.setEnabled(True)

        if not self.selected_tool_id or not self.env_manager.scan_results:
            self.btn_install.setEnabled(False)
            self.btn_check_updates.setEnabled(False)
            self.btn_upgrade.setEnabled(False)
            return

        tool_id = self.selected_tool_id
        tool_scan = self.env_manager.scan_results.get(tool_id, {})
        tool_dep = self.env_manager.dependency_results.get(tool_id, {})
        
        installed = tool_scan.get("installed", False)
        status = tool_dep.get("status")
        
        # Enable Install if not installed
        self.btn_install.setEnabled(not installed)
        
        # Enable Upgrade if installed and status is OUTDATED
        self.btn_upgrade.setEnabled(installed and status == "OUTDATED")
        
        # Enable check updates if installed
        self.btn_check_updates.setEnabled(installed)

    def on_table_selection(self):
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            self.selected_tool_id = None
            self.update_button_states()
            return
            
        row = selected_ranges[0].topRow()
        # The key is stored in the tool ID column or we can match from list of keys
        tool_keys = list(self.env_manager.tools_config.keys())
        if row < len(tool_keys):
            self.selected_tool_id = tool_keys[row]
        else:
            self.selected_tool_id = None
            
        self.update_button_states()

    # ---------------- EVENT HANDLERS ----------------

    def trigger_scan(self):
        self.update_log_panel("[INFO] Scanning environment... please wait.")
        self.btn_scan.setEnabled(False)
        self.btn_refresh.setEnabled(False)
        
        # Run scan in background thread to avoid GUI lag
        self.worker = ActionWorker(self.env_manager.scan_environment)
        self.worker.finished_signal.connect(self.on_scan_completed)
        self.worker.start()
        self.update_button_states()

    @Slot(dict)
    def on_scan_completed(self, results):
        self.update_log_panel("[SUCCESS] Environment scan completed.")
        self.populate_table()
        self.update_dashboard()
        self.worker = None
        self.update_button_states()

    def populate_table(self):
        self.table.setRowCount(0)
        tool_config = self.env_manager.tools_config
        scan_results = self.env_manager.scan_results
        dep_results = self.env_manager.dependency_results
        
        for tool_id, conf in tool_config.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            scan_res = scan_results.get(tool_id, {})
            dep_res = dep_results.get(tool_id, {})
            
            # Col 0: Tool
            self.table.setItem(row, 0, QTableWidgetItem(conf["display_name"]))
            
            # Col 1: Category
            self.table.setItem(row, 1, QTableWidgetItem(conf["category"]))
            
            # Col 2: Installed
            installed = scan_res.get("installed", False)
            inst_text = "Yes" if installed else "No"
            inst_item = QTableWidgetItem(inst_text)
            if installed:
                inst_item.setForeground(QColor("#2e7d32"))  # Dark Green
            else:
                inst_item.setForeground(QColor("#c62828"))  # Dark Red
            self.table.setItem(row, 2, inst_item)
            
            # Col 3: Version
            ver_text = scan_res.get("parsed_version") or scan_res.get("raw_version") or "-"
            # limit output size
            if len(ver_text) > 25:
                ver_text = ver_text[:22] + "..."
            self.table.setItem(row, 3, QTableWidgetItem(ver_text))
            
            # Col 4: Minimum Required
            self.table.setItem(row, 4, QTableWidgetItem(conf.get("minimum_version", "0.0.0")))
            
            # Col 5: Status
            status = dep_res.get("status", "UNKNOWN")
            msg = dep_res.get("message", "")
            status_item = QTableWidgetItem(status)
            status_item.setToolTip(msg)
            
            if status == "READY":
                status_item.setForeground(QColor("#2e7d32"))
            elif status == "OPTIONAL":
                status_item.setForeground(QColor("#757575"))
            elif status == "OUTDATED":
                status_item.setForeground(QColor("#ef6c00"))
            elif status in ("MISSING", "ERROR"):
                status_item.setForeground(QColor("#c62828"))
            else:
                status_item.setForeground(QColor("#ef6c00"))
                
            self.table.setItem(row, 5, status_item)

    def update_dashboard(self):
        summary = self.env_manager.get_status_summary()
        score = summary["score"]
        readiness = summary["readiness"]
        
        # Update Score Value
        self.score_val.setText(f"{score} / 100")
        
        # Update Overview Stats
        self.stats_val.setText(
            f"Installed: {summary['installed_count']} | Missing: {summary['missing_count']} (Total: {summary['total_count']})"
        )
        
        # Update Readiness Badge
        self.readiness_badge.setText(readiness)
        if readiness == "READY":
            self.readiness_badge.setStyleSheet(
                "background-color: #2e7d32; color: white; border-radius: 4px; font-weight: bold; font-size: 12px;"
            )
        elif readiness == "MOSTLY READY":
            self.readiness_badge.setStyleSheet(
                "background-color: #ef6c00; color: white; border-radius: 4px; font-weight: bold; font-size: 12px;"
            )
        else:
            self.readiness_badge.setStyleSheet(
                "background-color: #c62828; color: white; border-radius: 4px; font-weight: bold; font-size: 12px;"
            )

    def trigger_install(self):
        if not self.selected_tool_id:
            return
            
        tool_id = self.selected_tool_id
        tool_conf = self.env_manager.tools_config[tool_id]
        
        # Build command to show user
        cmd = self.env_manager.installer.build_install_command(tool_conf)
        if not cmd:
            QMessageBox.information(
                self,
                "Manual Installation Required",
                f"No automatic package installer mapped for {tool_conf['display_name']} on this platform.\n"
                "Please install this tool manually."
            )
            return
            
        cmd_str = " ".join(cmd)
        
        # Confirm prompt
        reply = QMessageBox.question(
            self,
            "Confirm Installation",
            f"Are you sure you want to install {tool_conf['display_name']}?\n\n"
            f"Command to execute:\n{cmd_str}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.update_log_panel(f"[INFO] Initializing installation for {tool_conf['display_name']}...")
            self.btn_scan.setEnabled(False)
            self.btn_refresh.setEnabled(False)
            self.btn_install.setEnabled(False)
            self.btn_upgrade.setEnabled(False)
            self.btn_check_updates.setEnabled(False)
            
            # Start installation in thread
            self.worker = ActionWorker(self.env_manager.install_tool, tool_id)
            self.worker.finished_signal.connect(self.on_install_completed)
            self.worker.start()

    @Slot(dict)
    def on_install_completed(self, result):
        tool_id = self.selected_tool_id
        if result.get("success"):
            self.update_log_panel(f"[SUCCESS] Tool installed successfully.")
            QMessageBox.information(self, "Installation Success", "The tool has been successfully installed and verified.")
        else:
            out = result.get("output", "Unknown error")
            self.update_log_panel(f"[ERROR] Tool installation failed: {out}")
            QMessageBox.critical(
                self,
                "Installation Failed",
                f"Installation failed.\n\nDetails:\n{out[:500]}"
            )
            
        self.worker = None
        self.populate_table()
        self.update_dashboard()
        self.update_button_states()

    def trigger_upgrade(self):
        if not self.selected_tool_id:
            return
            
        tool_id = self.selected_tool_id
        tool_conf = self.env_manager.tools_config[tool_id]
        
        # Build command to show user
        cmd = self.env_manager.updater.build_upgrade_command(tool_conf)
        if not cmd:
            QMessageBox.information(
                self,
                "Manual Upgrade Required",
                f"No automatic package upgrade mapped for {tool_conf['display_name']} on this platform.\n"
                "Please upgrade this tool manually."
            )
            return
            
        cmd_str = " ".join(cmd)
        
        # Confirm prompt
        reply = QMessageBox.question(
            self,
            "Confirm Upgrade",
            f"Are you sure you want to upgrade {tool_conf['display_name']}?\n\n"
            f"Command to execute:\n{cmd_str}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.update_log_panel(f"[INFO] Initializing upgrade for {tool_conf['display_name']}...")
            self.btn_scan.setEnabled(False)
            self.btn_refresh.setEnabled(False)
            self.btn_install.setEnabled(False)
            self.btn_upgrade.setEnabled(False)
            self.btn_check_updates.setEnabled(False)
            
            # Start upgrade in thread
            self.worker = ActionWorker(self.env_manager.upgrade_tool, tool_id)
            self.worker.finished_signal.connect(self.on_upgrade_completed)
            self.worker.start()

    @Slot(dict)
    def on_upgrade_completed(self, result):
        if result.get("success"):
            self.update_log_panel(f"[SUCCESS] Tool upgraded successfully.")
            QMessageBox.information(self, "Upgrade Success", "The tool has been successfully upgraded and verified.")
        else:
            out = result.get("output", "Unknown error")
            self.update_log_panel(f"[ERROR] Tool upgrade failed: {out}")
            QMessageBox.critical(
                self,
                "Upgrade Failed",
                f"Upgrade failed.\n\nDetails:\n{out[:500]}"
            )
            
        self.worker = None
        self.populate_table()
        self.update_dashboard()
        self.update_button_states()

    def trigger_check_updates(self):
        if not self.selected_tool_id:
            return
            
        tool_id = self.selected_tool_id
        tool_conf = self.env_manager.tools_config[tool_id]
        
        self.update_log_panel(f"[INFO] Checking for updates on '{tool_conf['display_name']}'...")
        
        self.worker = ActionWorker(self.env_manager.updater.check_update_available, tool_conf)
        self.worker.finished_signal.connect(self.on_check_updates_completed)
        self.worker.start()
        self.update_button_states()

    @Slot(object)
    def on_check_updates_completed(self, has_update):
        tool_id = self.selected_tool_id
        tool_conf = self.env_manager.tools_config[tool_id]
        
        if has_update is True:
            self.update_log_panel(f"[WARNING] An update IS available for '{tool_conf['display_name']}'.")
            QMessageBox.information(
                self,
                "Update Available",
                f"An update is available for {tool_conf['display_name']}.\n"
                "You can select the tool and click UPGRADE to update it."
            )
            # Mark dependency status as OUTDATED manually to reflect that it needs upgrade
            self.env_manager.dependency_results[tool_id]["status"] = "OUTDATED"
            self.env_manager.dependency_results[tool_id]["message"] = "An update is available on the package manager."
            self.populate_table()
        elif has_update is False:
            self.update_log_panel(f"[SUCCESS] '{tool_conf['display_name']}' is already up-to-date.")
            QMessageBox.information(
                self,
                "No Updates Found",
                f"{tool_conf['display_name']} is up-to-date."
            )
        else:
            self.update_log_panel(f"[WARNING] Could not check updates for '{tool_conf['display_name']}'.")
            QMessageBox.warning(
                self,
                "Check Updates Failed",
                f"Could not verify update availability for {tool_conf['display_name']}."
            )
            
        self.worker = None
        self.update_button_states()

