import PyInstaller.__main__
import os
import sys

def build():
    # Define paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Define Data Includes (Source, Destination)
    # PyInstaller expects 'Source:Dest' (Unix) or 'Source;Dest' (Windows)
    # BUT if we use PyInstaller.__main__, we can just pass the list of args
    # and let it handle separators if we manually construct the string, 
    # OR we can let it be careful.
    # Actually, the separator IS OS dependent even in args.
    
    sep = ';' if os.name == 'nt' else ':'
    
    datas = [
        (os.path.join(base_dir, "XML Vorlage"), "XML Vorlage"),
        (os.path.join(base_dir, "TariffDefinitions"), "TariffDefinitions"),
        (os.path.join(base_dir, "src", "ui", "styles.qss"), os.path.join("src", "ui"))
    ]
    
    add_data_args = []
    for src, dst in datas:
        # Check if source exists to avoid errors
        if os.path.exists(src):
            add_data_args.append(f'--add-data={src}{sep}{dst}')
        else:
            print(f"WARNING: Resource not found: {src}")

    # 2. PyInstaller Arguments
    args = [
        'main.py',                      # Script to build
        '--name=ORD_Tariff_Manager',    # Name of the executable
        '--onefile',                    # Single executable file
        '--windowed',                   # No console window (GUI mode)
        '--clean',                      # Clean cache
        '--noconfirm',                  # Overwrite output directory
        # '--hidden-import=pandas',     # Often needed, but PyInstaller is usually smart
    ] + add_data_args

    print("Building with arguments:", args)
    
    # 3. Run
    PyInstaller.__main__.run(args)

if __name__ == "__main__":
    build()
