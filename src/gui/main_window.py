import os
import sys
import subprocess
from datetime import datetime
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
    QFrame,
    QStackedWidget,
    QLineEdit,
    QComboBox,
    QDialog,
    QScrollArea,
    QSplitter
)
from PySide6.QtCore import Qt, QThread, Signal, Slot, QSize
from PySide6.QtGui import QFont, QColor, QClipboard, QGuiApplication

from src.core.environment_manager import EnvironmentManager
from src.utils.platform_utils import detect_platform, is_package_manager_available
from src.core.logger import ActionLogger

# Royal Engineering Console Color Palette
PALETTE = {
    "background": "#F5F2EA",
    "surface": "#FFFDF8",
    "primary": "#14213D",
    "primary_dark": "#0B132B",
    "accent": "#B08D57",
    "accent_light": "#D8C39A",
    "success": "#2E7D32",
    "warning": "#B7791F",
    "error": "#A33A3A",
    "text": "#1B1B1B",
    "muted": "#6B6B6B",
    "border": "#D6D0C4"
}

class ActionWorker(QThread):
    finished_signal = Signal(object)
    
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
            self.finished_signal.emit({"success": False, "output": f"Worker error: {e}"})

class MainWindow(QMainWindow):
    def __init__(self, config_path: str = None):
        super().__init__()
        self.setWindowTitle("eSim Environment Manager v2.0.0 — Royal Engineering Console")
        self.resize(1150, 750)
        self.setMinimumSize(950, 650)
        
        self.env_manager = EnvironmentManager(config_path)
        self.logger = ActionLogger.get_logger()
        
        self.selected_tool_id = None
        self.worker = None
        self.last_scan_time = "Never"

        # Apply global stylesheet
        self.setStyleSheet(self.get_global_stylesheet())
        
        # Build UI Structure
        self.setup_ui()
        
        # Perform initial scan automatically
        self.trigger_scan()

    def get_global_stylesheet(self) -> str:
        return f"""
            QMainWindow {{
                background-color: {PALETTE["background"]};
            }}
            QWidget {{
                font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
                color: {PALETTE["text"]};
            }}
            QFrame#Sidebar {{
                background-color: {PALETTE["primary"]};
                border: none;
            }}
            QPushButton.NavBtn {{
                background-color: transparent;
                color: {PALETTE["accent_light"]};
                border: none;
                border-radius: 4px;
                padding: 10px 15px;
                text-align: left;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton.NavBtn:hover {{
                background-color: rgba(176, 141, 87, 0.15);
                color: #FFFFFF;
            }}
            QPushButton.NavBtn:checked {{
                background-color: {PALETTE["accent"]};
                color: #FFFFFF;
                font-weight: bold;
            }}
            QFrame.Card {{
                background-color: {PALETTE["surface"]};
                border: 1px solid {PALETTE["border"]};
                border-radius: 6px;
            }}
            QTableWidget {{
                background-color: {PALETTE["surface"]};
                border: 1px solid {PALETTE["border"]};
                gridline-color: {PALETTE["border"]};
                selection-background-color: rgba(176, 141, 87, 0.2);
                selection-color: {PALETTE["primary"]};
            }}
            QHeaderView::section {{
                background-color: {PALETTE["primary"]};
                color: #FFFFFF;
                font-weight: bold;
                font-size: 12px;
                padding: 6px;
                border: none;
            }}
            QPushButton.PrimaryBtn {{
                background-color: {PALETTE["primary"]};
                color: #FFFFFF;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton.PrimaryBtn:hover {{
                background-color: {PALETTE["primary_dark"]};
            }}
            QPushButton.AccentBtn {{
                background-color: {PALETTE["accent"]};
                color: #FFFFFF;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton.AccentBtn:hover {{
                background-color: #967443;
            }}
        """

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        
        # ---------------- TOP HEADER ----------------
        header_frame = QFrame()
        header_frame.setFixedHeight(75)
        header_frame.setStyleSheet(f"background-color: {PALETTE['surface']}; border-bottom: 1px solid {PALETTE['border']};")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 10, 20, 10)
        
        title_box = QVBoxLayout()
        app_title = QLabel("eSim Environment Manager v2.0.0")
        app_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        app_subtitle = QLabel("Royal Engineering Console — Open-Source EDA Environment Intelligence")
        app_subtitle.setStyleSheet(f"color: {PALETTE['muted']}; font-size: 11px;")
        title_box.addWidget(app_title)
        title_box.addWidget(app_subtitle)
        header_layout.addLayout(title_box)
        
        header_layout.addStretch()
        
        # Top Header Info Items
        plat_str = detect_platform().capitalize()
        self.top_os_badge = QLabel(f"OS: {plat_str}")
        self.top_os_badge.setStyleSheet(f"background-color: #E2DDD0; color: {PALETTE['primary']}; padding: 5px 10px; border-radius: 4px; font-weight: bold; font-size: 11px;")
        header_layout.addWidget(self.top_os_badge)
        
        self.top_last_scan = QLabel("Last Scan: Pending")
        self.top_last_scan.setStyleSheet(f"color: {PALETTE['muted']}; font-size: 11px; margin-left: 10px;")
        header_layout.addWidget(self.top_last_scan)
        
        self.top_readiness_badge = QLabel("INITIALIZING")
        self.top_readiness_badge.setAlignment(Qt.AlignCenter)
        self.top_readiness_badge.setFixedWidth(130)
        self.top_readiness_badge.setFixedHeight(32)
        self.top_readiness_badge.setStyleSheet("background-color: #757575; color: white; border-radius: 4px; font-weight: bold; font-size: 11px;")
        header_layout.addWidget(self.top_readiness_badge)
        
        root_layout.addWidget(header_frame)
        
        # ---------------- MAIN CONTENT SPLITTER (Sidebar + Stack) ----------------
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        
        # Sidebar
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("Sidebar")
        sidebar_frame.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(10, 15, 10, 15)
        sidebar_layout.setSpacing(8)
        
        nav_title = QLabel("NAVIGATION")
        nav_title.setStyleSheet(f"color: {PALETTE['accent_light']}; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        sidebar_layout.addWidget(nav_title)
        
        self.nav_buttons = {}
        pages = [
            ("dashboard", "📊 Dashboard"),
            ("inventory", "🛠️ Tool Inventory"),
            ("profiles", "🧩 EDA Profiles"),
            ("dependencies", "🔍 Dependencies"),
            ("installer", "🚀 Install / Update"),
            ("logs", "📜 Activity Log")
        ]
        
        for pid, label in pages:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setProperty("class", "NavBtn")
            btn.clicked.connect(lambda checked, p=pid: self.switch_page(p))
            sidebar_layout.addWidget(btn)
            self.nav_buttons[pid] = btn
            
        sidebar_layout.addStretch()
        
        version_info = QLabel("FOSSEE eSim Task 5\nv2.0.0 Production")
        version_info.setStyleSheet(f"color: {PALETTE['accent_light']}; font-size: 10px; opacity: 0.7;")
        sidebar_layout.addWidget(version_info)
        
        body_layout.addWidget(sidebar_frame)
        
        # Stacked Pages
        self.stack = QStackedWidget()
        
        self.page_dashboard = self.build_dashboard_page()
        self.page_inventory = self.build_inventory_page()
        self.page_profiles = self.build_profiles_page()
        self.page_dependencies = self.build_dependencies_page()
        self.page_installer = self.build_installer_page()
        self.page_logs = self.build_logs_page()
        
        self.stack.addWidget(self.page_dashboard)    # Index 0
        self.stack.addWidget(self.page_inventory)    # Index 1
        self.stack.addWidget(self.page_profiles)     # Index 2
        self.stack.addWidget(self.page_dependencies) # Index 3
        self.stack.addWidget(self.page_installer)    # Index 4
        self.stack.addWidget(self.page_logs)         # Index 5
        
        body_layout.addWidget(self.stack)
        root_layout.addLayout(body_layout)
        
        # Set default page
        self.switch_page("dashboard")

    def switch_page(self, page_id: str):
        mapping = {
            "dashboard": 0,
            "inventory": 1,
            "profiles": 2,
            "dependencies": 3,
            "installer": 4,
            "logs": 5
        }
        idx = mapping.get(page_id, 0)
        self.stack.setCurrentIndex(idx)
        
        for pid, btn in self.nav_buttons.items():
            btn.setChecked(pid == page_id)

    # ---------------- PAGE 1: DASHBOARD PAGE ----------------
    def build_dashboard_page(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Top KPI Cards Row
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(15)
        
        # Health Score Card
        self.card_health = QFrame()
        self.card_health.setProperty("class", "Card")
        ch_layout = QVBoxLayout(self.card_health)
        ch_title = QLabel("ENVIRONMENT HEALTH")
        ch_title.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {PALETTE['muted']};")
        self.val_health_score = QLabel("N/A")
        self.val_health_score.setFont(QFont("Segoe UI", 26, QFont.Bold))
        self.val_health_sub = QLabel("Scanning...")
        self.val_health_sub.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {PALETTE['accent']};")
        
        btn_explain_score = QPushButton("View Deduction Details")
        btn_explain_score.setStyleSheet(f"background: transparent; color: {PALETTE['primary']}; font-size: 11px; font-weight: bold; text-align: left; text-decoration: underline;")
        btn_explain_score.clicked.connect(lambda: self.switch_page("dependencies"))
        
        ch_layout.addWidget(ch_title)
        ch_layout.addWidget(self.val_health_score)
        ch_layout.addWidget(self.val_health_sub)
        ch_layout.addWidget(btn_explain_score)
        
        # Tools Overview Card
        self.card_tools = QFrame()
        self.card_tools.setProperty("class", "Card")
        ct_layout = QVBoxLayout(self.card_tools)
        ct_title = QLabel("TOOL INVENTORY SUMMARY")
        ct_title.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {PALETTE['muted']};")
        self.val_tools_summary = QLabel("0 Installed / 0 Total")
        self.val_tools_summary.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.val_tools_sub = QLabel("Categories: Core, PCB, Simulation, Digital, VLSI")
        self.val_tools_sub.setStyleSheet(f"font-size: 11px; color: {PALETTE['muted']};")
        
        ct_layout.addWidget(ct_title)
        ct_layout.addWidget(self.val_tools_summary)
        ct_layout.addWidget(self.val_tools_sub)
        
        # Package Manager Card
        self.card_pm = QFrame()
        self.card_pm.setProperty("class", "Card")
        cpm_layout = QVBoxLayout(self.card_pm)
        cpm_title = QLabel("PACKAGE MANAGER INTEGRATION")
        cpm_title.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {PALETTE['muted']};")
        
        plat = detect_platform().capitalize()
        pm_name = "winget" if plat == "Windows" else ("brew" if plat == "Macos" else "apt")
        pm_avail = "Detected" if is_package_manager_available() else "Not Found"
        self.val_pm = QLabel(f"{pm_name}: {pm_avail}")
        self.val_pm.setFont(QFont("Segoe UI", 15, QFont.Bold))
        self.val_pm_sub = QLabel(f"Platform: {plat}")
        self.val_pm_sub.setStyleSheet(f"font-size: 11px; color: {PALETTE['muted']};")
        
        cpm_layout.addWidget(cpm_title)
        cpm_layout.addWidget(self.val_pm)
        cpm_layout.addWidget(self.val_pm_sub)
        
        kpi_layout.addWidget(self.card_health)
        kpi_layout.addWidget(self.card_tools)
        kpi_layout.addWidget(self.card_pm)
        layout.addLayout(kpi_layout)
        
        # Actions Control Bar
        actions_card = QFrame()
        actions_card.setProperty("class", "Card")
        ac_layout = QHBoxLayout(actions_card)
        ac_layout.setContentsMargins(15, 12, 15, 12)
        
        lbl_act = QLabel("QUICK ACTIONS")
        lbl_act.setFont(QFont("Segoe UI", 11, QFont.Bold))
        ac_layout.addWidget(lbl_act)
        
        ac_layout.addStretch()
        
        self.btn_dash_scan = QPushButton("SCAN ENVIRONMENT")
        self.btn_dash_scan.setProperty("class", "AccentBtn")
        self.btn_dash_scan.clicked.connect(self.trigger_scan)
        ac_layout.addWidget(self.btn_dash_scan)
        
        self.btn_dash_check = QPushButton("CHECK ALL UPDATES")
        self.btn_dash_check.setProperty("class", "PrimaryBtn")
        self.btn_dash_check.clicked.connect(self.trigger_check_all_updates)
        ac_layout.addWidget(self.btn_dash_check)
        
        layout.addWidget(actions_card)
        
        # Category Cards Overview
        lbl_cats = QLabel("EDA CATEGORY INVENTORY")
        lbl_cats.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(lbl_cats)
        
        self.cat_cards_layout = QHBoxLayout()
        self.cat_cards_layout.setSpacing(10)
        layout.addLayout(self.cat_cards_layout)
        
        layout.addStretch()
        return widget

    # ---------------- PAGE 2: TOOL INVENTORY PAGE ----------------
    def build_inventory_page(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Search and Filter bar
        filter_layout = QHBoxLayout()
        
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Search tools by name, category, or command...")
        self.txt_search.textChanged.connect(self.apply_table_filters)
        filter_layout.addWidget(self.txt_search, stretch=2)
        
        self.combo_category = QComboBox()
        self.combo_category.addItems(["All Categories", "Core", "Development", "PCB", "Simulation", "Digital Design", "Open VLSI", "FPGA", "Formal Verification"])
        self.combo_category.currentTextChanged.connect(self.apply_table_filters)
        filter_layout.addWidget(self.combo_category, stretch=1)
        
        self.combo_status = QComboBox()
        self.combo_status.addItems(["All Statuses", "READY", "MISSING", "OUTDATED", "OPTIONAL"])
        self.combo_status.currentTextChanged.connect(self.apply_table_filters)
        filter_layout.addWidget(self.combo_status, stretch=1)
        
        layout.addLayout(filter_layout)
        
        # Table & Inspector Splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Main Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Tool", "Category", "Importance", "Version", "Min Required", "Status", "Detection Source"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self.on_inventory_selection)
        splitter.addWidget(self.table)
        
        # Tool Detail Inspector Drawer
        self.inspector_card = QFrame()
        self.inspector_card.setProperty("class", "Card")
        self.inspector_card.setMinimumWidth(300)
        insp_layout = QVBoxLayout(self.inspector_card)
        insp_layout.setContentsMargins(15, 15, 15, 15)
        
        insp_title = QLabel("TOOL DETAIL INSPECTOR")
        insp_title.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {PALETTE['accent']}; letter-spacing: 1px;")
        insp_layout.addWidget(insp_title)
        
        self.insp_tool_name = QLabel("Select a tool to inspect")
        self.insp_tool_name.setFont(QFont("Segoe UI", 16, QFont.Bold))
        insp_layout.addWidget(self.insp_tool_name)
        
        self.insp_details_text = QTextEdit()
        self.insp_details_text.setReadOnly(True)
        self.insp_details_text.setStyleSheet(f"background-color: {PALETTE['background']}; border: 1px solid {PALETTE['border']}; font-size: 12px;")
        insp_layout.addWidget(self.insp_details_text)
        
        insp_btns = QVBoxLayout()
        
        self.btn_insp_open_loc = QPushButton("Open File Location")
        self.btn_insp_open_loc.setProperty("class", "PrimaryBtn")
        self.btn_insp_open_loc.clicked.connect(self.trigger_open_location)
        insp_btns.addWidget(self.btn_insp_open_loc)
        
        self.btn_insp_install = QPushButton("Install Tool")
        self.btn_insp_install.setProperty("class", "AccentBtn")
        self.btn_insp_install.clicked.connect(self.trigger_install_selected)
        insp_btns.addWidget(self.btn_insp_install)
        
        self.btn_insp_upgrade = QPushButton("Upgrade Tool")
        self.btn_insp_upgrade.setProperty("class", "AccentBtn")
        self.btn_insp_upgrade.clicked.connect(self.trigger_upgrade_selected)
        insp_btns.addWidget(self.btn_insp_upgrade)
        
        insp_layout.addLayout(insp_btns)
        splitter.addWidget(self.inspector_card)
        
        splitter.setSizes([700, 300])
        layout.addWidget(splitter)
        return widget

    # ---------------- PAGE 3: EDA PROFILES PAGE ----------------
    def build_profiles_page(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        lbl_head = QLabel("EDA WORKFLOW PROFILES EVALUATION")
        lbl_head.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(lbl_head)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        self.profiles_container = QWidget()
        self.profiles_layout = QVBoxLayout(self.profiles_container)
        self.profiles_layout.setSpacing(15)
        
        scroll.setWidget(self.profiles_container)
        layout.addWidget(scroll)
        return widget

    # ---------------- PAGE 4: DEPENDENCIES & SCORE PAGE ----------------
    def build_dependencies_page(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        lbl_head = QLabel("TRANSPARENT DEPENDENCY & SCORE DEDUCTION BREAKDOWN")
        lbl_head.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(lbl_head)
        
        card_reasons = QFrame()
        card_reasons.setProperty("class", "Card")
        cr_layout = QVBoxLayout(card_reasons)
        
        self.txt_reasons = QTextEdit()
        self.txt_reasons.setReadOnly(True)
        self.txt_reasons.setStyleSheet(f"font-size: 13px; line-height: 1.6; background: {PALETTE['surface']};")
        cr_layout.addWidget(self.txt_reasons)
        
        layout.addWidget(card_reasons)
        return widget

    # ---------------- PAGE 5: INSTALLER / UPDATER PAGE ----------------
    def build_installer_page(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        lbl_head = QLabel("SAFE PACKAGE MANAGER INSTALLATION & UPGRADE ENGINE")
        lbl_head.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(lbl_head)
        
        lbl_sub = QLabel("Select any missing or outdated tool below to preview and execute platform package manager commands.")
        lbl_sub.setStyleSheet(f"color: {PALETTE['muted']}; font-size: 12px;")
        layout.addWidget(lbl_sub)
        
        self.installer_table = QTableWidget()
        self.installer_table.setColumnCount(5)
        self.installer_table.setHorizontalHeaderLabels([
            "Tool", "Category", "Status", "Package Identifier", "Proposed Action"
        ])
        self.installer_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.installer_table)
        
        return widget

    # ---------------- PAGE 6: ACTIVITY LOG PAGE ----------------
    def build_logs_page(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        log_head = QHBoxLayout()
        lbl_log = QLabel("AUDIT & ACTIVITY LOG")
        lbl_log.setFont(QFont("Segoe UI", 14, QFont.Bold))
        log_head.addWidget(lbl_log)
        log_head.addStretch()
        
        btn_clr = QPushButton("Clear Log View")
        btn_clr.clicked.connect(self.clear_logs)
        log_head.addWidget(btn_clr)
        
        layout.addLayout(log_head)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet(f"background-color: {PALETTE['primary']}; color: #F8F9FA; font-family: Consolas, monospace; font-size: 12px;")
        layout.addWidget(self.log_text)
        
        return widget

    # ---------------- LOGIC & UPDATES ----------------

    def append_log(self, msg: str):
        self.log_text.append(msg)
        self.log_text.ensureCursorVisible()

    def clear_logs(self):
        self.log_text.clear()

    def trigger_scan(self):
        self.append_log(f"[{datetime.now().strftime('%H:%M:%S')}] Launching 5-tier tool discovery pipeline...")
        self.btn_dash_scan.setEnabled(False)
        
        self.worker = ActionWorker(self.env_manager.scan_environment)
        self.worker.finished_signal.connect(self.on_scan_completed)
        self.worker.start()

    @Slot(object)
    def on_scan_completed(self, results):
        self.last_scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.top_last_scan.setText(f"Last Scan: {datetime.now().strftime('%H:%M:%S')}")
        self.append_log(f"[{datetime.now().strftime('%H:%M:%S')}] Discovery pipeline complete.")
        
        self.update_dashboard_view()
        self.update_inventory_table()
        self.update_profiles_view()
        self.update_dependencies_view()
        self.update_installer_view()
        
        self.btn_dash_scan.setEnabled(True)
        self.worker = None

    def update_dashboard_view(self):
        summary = self.env_manager.get_status_summary()
        score = summary["score"]
        readiness = summary["readiness"]
        
        self.val_health_score.setText(f"{score} / 100")
        self.val_health_sub.setText(f"READINESS: {readiness}")
        self.val_tools_summary.setText(f"{summary['installed_count']} Installed / {summary['total_count']} Configured")
        
        # Header Badge
        self.top_readiness_badge.setText(readiness)
        if readiness == "READY":
            self.top_readiness_badge.setStyleSheet(f"background-color: {PALETTE['success']}; color: white; border-radius: 4px; font-weight: bold; font-size: 11px;")
        elif readiness == "MOSTLY READY":
            self.top_readiness_badge.setStyleSheet(f"background-color: {PALETTE['warning']}; color: white; border-radius: 4px; font-weight: bold; font-size: 11px;")
        else:
            self.top_readiness_badge.setStyleSheet(f"background-color: {PALETTE['error']}; color: white; border-radius: 4px; font-weight: bold; font-size: 11px;")
            
        # Clear category cards
        while self.cat_cards_layout.count():
            child = self.cat_cards_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        # Group tools by category
        categories = {}
        for tool_id, tool_data in self.env_manager.scan_results.items():
            cat = tool_data.get("category", "Other")
            categories.setdefault(cat, []).append(tool_data)
            
        for cat_name, cat_tools in categories.items():
            card = QFrame()
            card.setProperty("class", "Card")
            c_layout = QVBoxLayout(card)
            
            c_title = QLabel(cat_name.upper())
            c_title.setStyleSheet(f"font-size: 10px; font-weight: bold; color: {PALETTE['accent']};")
            
            installed_cnt = sum(1 for t in cat_tools if t.get("installed"))
            c_val = QLabel(f"{installed_cnt} / {len(cat_tools)} Installed")
            c_val.setFont(QFont("Segoe UI", 12, QFont.Bold))
            
            c_layout.addWidget(c_title)
            c_layout.addWidget(c_val)
            self.cat_cards_layout.addWidget(card)

    def update_inventory_table(self):
        self.table.setRowCount(0)
        scan_results = self.env_manager.scan_results
        dep_results = self.env_manager.dependency_results
        
        for tool_id, tool in scan_results.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            dep = dep_results.get(tool_id, {})
            
            # Col 0: Tool ID & Name
            item_name = QTableWidgetItem(tool.get("display_name", tool_id))
            item_name.setData(Qt.UserRole, tool_id)
            self.table.setItem(row, 0, item_name)
            
            # Col 1: Category
            self.table.setItem(row, 1, QTableWidgetItem(tool.get("category", "-")))
            
            # Col 2: Importance
            imp = tool.get("importance", "RECOMMENDED")
            self.table.setItem(row, 2, QTableWidgetItem(imp))
            
            # Col 3: Version
            ver = tool.get("parsed_version") or tool.get("raw_version") or "-"
            if len(ver) > 20: ver = ver[:17] + "..."
            self.table.setItem(row, 3, QTableWidgetItem(ver))
            
            # Col 4: Min Required
            self.table.setItem(row, 4, QTableWidgetItem(tool.get("minimum_version", "-")))
            
            # Col 5: Status
            status = dep.get("status", "UNKNOWN")
            status_item = QTableWidgetItem(status)
            if status == "READY":
                status_item.setForeground(QColor(PALETTE["success"]))
            elif status == "OUTDATED":
                status_item.setForeground(QColor(PALETTE["warning"]))
            elif status in ("MISSING", "ERROR"):
                status_item.setForeground(QColor(PALETTE["error"]))
            else:
                status_item.setForeground(QColor(PALETTE["muted"]))
            self.table.setItem(row, 5, status_item)
            
            # Col 6: Detection Source & Confidence
            src = tool.get("source", "NOT_FOUND")
            conf = tool.get("confidence", 0)
            self.table.setItem(row, 6, QTableWidgetItem(f"{src} ({conf}%)"))

    def apply_table_filters(self):
        query = self.txt_search.text().lower()
        cat_filter = self.combo_category.currentText()
        status_filter = self.combo_status.currentText()
        
        for row in range(self.table.rowCount()):
            tool_name = self.table.item(row, 0).text().lower()
            cat = self.table.item(row, 1).text()
            status = self.table.item(row, 5).text()
            
            match_query = query in tool_name or query in cat.lower()
            match_cat = (cat_filter == "All Categories") or (cat_filter == cat)
            match_status = (status_filter == "All Statuses") or (status_filter == status)
            
            self.table.setRowHidden(row, not (match_query and match_cat and match_status))

    def on_inventory_selection(self):
        ranges = self.table.selectedRanges()
        if not ranges:
            self.selected_tool_id = None
            self.insp_tool_name.setText("Select a tool to inspect")
            self.insp_details_text.clear()
            return
            
        row = ranges[0].topRow()
        tool_id = self.table.item(row, 0).data(Qt.UserRole)
        self.selected_tool_id = tool_id
        
        tool = self.env_manager.scan_results.get(tool_id, {})
        dep = self.env_manager.dependency_results.get(tool_id, {})
        
        self.insp_tool_name.setText(tool.get("display_name", tool_id))
        
        details = (
            f"ID: {tool_id}\n"
            f"Category: {tool.get('category', '-')}\n"
            f"Importance: {tool.get('importance', '-')}\n"
            f"Installed: {'YES' if tool.get('installed') else 'NO'}\n"
            f"Status: {dep.get('status', '-')}\n"
            f"Detected Version: {tool.get('parsed_version') or '-'}\n"
            f"Minimum Version: {tool.get('minimum_version', '-')}\n"
            f"Executable Path: {tool.get('executable_path') or 'Not Found'}\n"
            f"Detection Source: {tool.get('source', '-')}\n"
            f"Confidence: {tool.get('confidence', 0)}%\n"
            f"Error Details: {tool.get('error') or 'None'}\n"
        )
        self.insp_details_text.setText(details)
        
        # Button availability
        self.btn_insp_open_loc.setEnabled(bool(tool.get("executable_path")))
        self.btn_insp_install.setEnabled(not tool.get("installed"))
        self.btn_insp_upgrade.setEnabled(tool.get("installed") and dep.get("status") == "OUTDATED")

    def trigger_open_location(self):
        if not self.selected_tool_id: return
        tool = self.env_manager.scan_results.get(self.selected_tool_id, {})
        path = tool.get("executable_path")
        if path and os.path.exists(path):
            folder = os.path.dirname(path)
            if detect_platform() == "windows":
                os.startfile(folder)
            elif detect_platform() == "macos":
                subprocess.run(["open", folder])
            else:
                subprocess.run(["xdg-open", folder])

    def trigger_install_selected(self):
        if not self.selected_tool_id: return
        tool_id = self.selected_tool_id
        tool_conf = self.env_manager.tools_config[tool_id]
        
        cmd = self.env_manager.installer.build_install_command(tool_conf)
        if not cmd:
            QMessageBox.information(self, "Manual Install", f"No package manager mapping for '{tool_id}' on this platform.")
            return
            
        reply = QMessageBox.question(self, "Confirm Installation", f"Install {tool_conf['display_name']}?\nCommand: {' '.join(cmd)}")
        if reply == QMessageBox.Yes:
            self.append_log(f"[{datetime.now().strftime('%H:%M:%S')}] Installing {tool_id}...")
            self.worker = ActionWorker(self.env_manager.install_tool, tool_id)
            self.worker.finished_signal.connect(self.on_action_finished)
            self.worker.start()

    def trigger_upgrade_selected(self):
        if not self.selected_tool_id: return
        tool_id = self.selected_tool_id
        tool_conf = self.env_manager.tools_config[tool_id]
        
        cmd = self.env_manager.updater.build_upgrade_command(tool_conf)
        if not cmd:
            QMessageBox.information(self, "Manual Upgrade", f"No upgrade command available for '{tool_id}'.")
            return
            
        reply = QMessageBox.question(self, "Confirm Upgrade", f"Upgrade {tool_conf['display_name']}?\nCommand: {' '.join(cmd)}")
        if reply == QMessageBox.Yes:
            self.append_log(f"[{datetime.now().strftime('%H:%M:%S')}] Upgrading {tool_id}...")
            self.worker = ActionWorker(self.env_manager.upgrade_tool, tool_id)
            self.worker.finished_signal.connect(self.on_action_finished)
            self.worker.start()

    @Slot(object)
    def on_action_finished(self, result):
        self.append_log(f"[{datetime.now().strftime('%H:%M:%S')}] Action result: {result}")
        self.worker = None
        self.trigger_scan()

    def trigger_check_all_updates(self):
        self.append_log(f"[{datetime.now().strftime('%H:%M:%S')}] Checking package updates across installed tools...")
        # Simple scan refresh
        self.trigger_scan()

    # ---------------- VIEW UPDATING ----------------
    def update_profiles_view(self):
        evals = self.env_manager.profile_evaluations
        
        while self.profiles_layout.count():
            child = self.profiles_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
            
        for pid, peval in evals.items():
            card = QFrame()
            card.setProperty("class", "Card")
            c_layout = QVBoxLayout(card)
            
            head = QHBoxLayout()
            lbl_n = QLabel(peval["name"])
            lbl_n.setFont(QFont("Segoe UI", 14, QFont.Bold))
            head.addWidget(lbl_n)
            
            head.addStretch()
            
            badge = QLabel(f"{peval['readiness']} ({peval['score']}%)")
            badge.setStyleSheet(f"background: {PALETTE['primary']}; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;")
            head.addWidget(badge)
            c_layout.addLayout(head)
            
            lbl_d = QLabel(peval["description"])
            lbl_d.setStyleSheet(f"color: {PALETTE['muted']}; font-size: 11px;")
            c_layout.addWidget(lbl_d)
            
            lbl_stats = QLabel(f"Required Tools: {peval['required_count']} | Recommended Tools: {peval['recommended_count']}")
            lbl_stats.setFont(QFont("Segoe UI", 10, QFont.Bold))
            c_layout.addWidget(lbl_stats)
            
            reasons_txt = "\n".join([f"• {r}" for r in peval["reasons"]])
            txt_r = QTextEdit()
            txt_r.setReadOnly(True)
            txt_r.setFixedHeight(60)
            txt_r.setText(reasons_txt)
            c_layout.addWidget(txt_r)
            
            self.profiles_layout.addWidget(card)

    def update_dependencies_view(self):
        reasons = self.env_manager.get_score_reasons()
        formatted = "DETAILED ENVIRONMENT HEALTH DEDUCTION LOG\n" + "="*50 + "\n\n"
        formatted += "\n".join([f"[-] {r}" for r in reasons])
        self.txt_reasons.setText(formatted)

    def update_installer_view(self):
        self.installer_table.setRowCount(0)
        scan = self.env_manager.scan_results
        
        for tool_id, tool in scan.items():
            if not tool.get("installed") or self.env_manager.dependency_results.get(tool_id, {}).get("status") == "OUTDATED":
                row = self.installer_table.rowCount()
                self.installer_table.insertRow(row)
                
                self.installer_table.setItem(row, 0, QTableWidgetItem(tool.get("display_name", tool_id)))
                self.installer_table.setItem(row, 1, QTableWidgetItem(tool.get("category", "-")))
                
                st = self.env_manager.dependency_results.get(tool_id, {}).get("status", "MISSING")
                self.installer_table.setItem(row, 2, QTableWidgetItem(st))
                
                pkgs = tool.get("packages", {})
                pkg_id = pkgs.get(detect_platform(), "Manual")
                self.installer_table.setItem(row, 3, QTableWidgetItem(pkg_id))
                
                act = "Install" if st == "MISSING" or st == "OPTIONAL" else "Upgrade"
                self.installer_table.setItem(row, 4, QTableWidgetItem(act))
