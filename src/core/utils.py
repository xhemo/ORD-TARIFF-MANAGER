import sys
import os

def get_base_path():
    """
    Get the base path of the application.
    If frozen (bundled by PyInstaller), using sys._MEIPASS.
    Otherwise, using the project root directory.
    """
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle, the PyInstaller bootloader
        # extends the sys module by a flag frozen=True and sets the app 
        # path into variable _MEIPASS.
        return sys._MEIPASS
    else:
        # If running from source, go up 3 levels from this file:
        # src/core/utils.py -> src/core -> src -> (project root)
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_resource_path(relative_path):
    """
    Get the absolute path to a resource, works for dev and for PyInstaller.
    relative_path: Path relative to the project root (e.g., 'styles.qss' or 'TariffDefinitions/foo.json')
    """
    base_path = get_base_path()
    return os.path.join(base_path, relative_path)
