import sys
import os
from PySide6.QtWidgets import QApplication

# Add 'src' directory to sys.path so we can import from ui, core, etc.
# Check if we are running in a frozen bundle (PyInstaller)
if getattr(sys, 'frozen', False):
    # In frozen mode, PyInstaller should have bundled 'ui' and 'core' as top-level modules 
    # IF we set paths correctly. 
    pass
else:
    # Running from source
    src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
    sys.path.append(src_path)

try:
    from ui.main_window import MainWindow
except ImportError:
    # Fallback: maybe we are in a structure where 'src' is a package
    from src.ui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.showMaximized()
    
    sys.exit(app.exec())
