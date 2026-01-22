import sys
import os
from PySide6.QtWidgets import QApplication

# Add 'src' directory to sys.path so we can import from ui, core, etc.
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
sys.path.append(src_path)

from ui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.showMaximized()
    
    sys.exit(app.exec())
