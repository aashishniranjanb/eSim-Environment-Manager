import sys
from PySide6.QtWidgets import QApplication
from src.gui.main_window import MainWindow

def run(config_path: str = None):
    """Launches the PySide6 Graphical User Interface for ESEM.
    
    Args:
        config_path (str): Optional path to custom tools configuration file.
    """
    app = QApplication(sys.argv)
    window = MainWindow(config_path)
    window.show()
    sys.exit(app.exec())