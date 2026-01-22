from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, 
                               QMessageBox, QApplication, QTableWidget, QTableWidgetItem, 
                               QFrame, QFormLayout, QComboBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPixmap, QPainter, QIcon
import re

class MatrixImportDialog(QDialog):
    def __init__(self, current_columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tarif aus Zwischenablage einfügen")
        self.resize(900, 650)
        self.current_columns = current_columns
        self.result_data = [] # List of dicts
        
        # Main Layout
        self.main_layout = QVBoxLayout(self)
        
        # Content placeholder (we swap this between "Help View" and "Import View")
        self.content_widget = QWidget()
        self.main_layout.addWidget(self.content_widget)
        
        # Initial Load
        self.load_from_clipboard()

    def load_from_clipboard(self):
        # 1. Clear previous content
        if self.content_widget.layout():
            # Clear existing layout items
            old_layout = self.content_widget.layout()
            while old_layout.count():
                child = old_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            QWidget().setLayout(old_layout) # Force delete old layout
        
        # New Layout for content
        layout = QVBoxLayout(self.content_widget)
        
        # 2. Get Data
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        
        self.rows = []
        lines = text.split('\n')
        for line in lines:
            line = line.rstrip('\r\n')
            if not line: continue
            self.rows.append(line.split('\t'))
                
        # 3. Decision: Empty or Data?
        if not self.rows:
            self.show_tutorial_view(layout)
        else:
            self.show_data_view(layout)

    def show_tutorial_view(self, layout):
        # Center everything
        layout.addStretch()
        
        # Icon or Big Text
        title = QLabel("📋 Keine Daten in der Zwischenablage")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #ff9800;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Explanation
        instr = QLabel(
            "Die Zwischenablage scheint leer zu sein oder enthält keine Tabelle.\n\n"
            "So funktioniert der Import:\n"
            "1. Öffnen Sie Ihre Excel- oder CSV-Datei.\n"
            "2. Markieren Sie die gesamte Tabelle inkl. Kopfzeilen.\n"
            "3. Drücken Sie Cmd+C (Kopieren).\n"
            "4. Klicken Sie unten auf 'Erneut prüfen'."
        )
        instr.setStyleSheet("font-size: 14px; line-height: 1.5; color: #ccc;")
        instr.setAlignment(Qt.AlignCenter)
        layout.addWidget(instr)
        
        layout.addSpacing(30)
        
        # Retry Button
        retry_btn = QPushButton("🔄 Jetzt erneut prüfen")
        retry_btn.setFixedWidth(200)
        retry_btn.setStyleSheet("background-color: #2196f3; color: white; padding: 12px; font-weight: bold; font-size: 14px;")
        retry_btn.clicked.connect(self.load_from_clipboard)
        
        # Center button
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_box.addWidget(retry_btn)
        btn_box.addStretch()
        layout.addLayout(btn_box)
        
        layout.addStretch()
        
        # Cancel at bottom
        cancel_box = QHBoxLayout()
        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.clicked.connect(self.reject)
        cancel_box.addWidget(cancel_btn)
        cancel_box.addStretch()
        layout.addLayout(cancel_box)

    def show_data_view(self, layout):
        # Instructions
        layout.addWidget(QLabel("Überprüfen Sie die Daten aus der Zwischenablage:"))
        
        # Table Preview
        self.table = QTableWidget()
        self.table.setRowCount(len(self.rows))
        self.table.setColumnCount(len(self.rows[0]))
        
        for i, row in enumerate(self.rows):
            for j, val in enumerate(row):
                # Clean value for display
                try:
                    cleaned_val = self.clean_number(val)
                    if isinstance(cleaned_val, float):
                        if cleaned_val.is_integer():
                             display_text = str(int(cleaned_val))
                        else:
                             display_text = f"{cleaned_val:.2f}"
                    else:
                        display_text = str(cleaned_val)
                except:
                    display_text = val # Fallback

                item = QTableWidgetItem(display_text)
                
                # Check for "empty" top-left corner
                if i == 0 and j == 0 and not display_text.strip():
                     item.setBackground(QColor("#263238")) # Dark corner
                
                # Header Styling (First Row and First Column)
                elif i == 0: # Top Header
                    item.setBackground(QColor("#37474f")) # Darker Slate
                    item.setForeground(QColor("#eceff1")) # Light Text
                    item.setFont(QFont("Arial", 10, QFont.Bold))
                    item.setTextAlignment(Qt.AlignCenter)
                elif j == 0: # Left Header
                    item.setBackground(QColor("#37474f")) # Darker Slate
                    item.setForeground(QColor("#eceff1"))
                    item.setFont(QFont("Arial", 10, QFont.Bold))
                    item.setTextAlignment(Qt.AlignCenter)
                else:
                    item.setTextAlignment(Qt.AlignCenter)
                
                self.table.setItem(i, j, item)
        
        layout.addWidget(self.table)
        
        # Mapping Controls
        map_group = QFrame()
        map_layout = QFormLayout(map_group)
        
        self.combo_top = QComboBox()
        self.combo_top.addItems(["(Ignorieren)"] + self.current_columns)
        # Default: Always take first two columns
        if len(self.current_columns) > 0:
            self.combo_top.setCurrentIndex(1) # 1st column
            
        self.combo_left = QComboBox()
        self.combo_left.addItems(["(Ignorieren)"] + self.current_columns)
        
        if len(self.current_columns) > 1:
            self.combo_left.setCurrentIndex(2) # 2nd column
            
        map_layout.addRow("Header (Oben):", self.combo_top)
        map_layout.addRow("Header (Links):", self.combo_left)
        
        layout.addWidget(map_group)
        layout.addWidget(QLabel("Die Zellenwerte werden automatisch bereinigt (z.B. '31,27 €' -> 31.27)."))

        # Buttons
        btn_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.clicked.connect(self.reject)
        
        self.replace_btn = QPushButton("🔄 Werte ersetzen")
        self.replace_btn.clicked.connect(self.on_replace)
        self.replace_btn.setToolTip("Löscht die aktuelle Tabelle und fügt diese Werte ein.")
        
        self.append_btn = QPushButton(" Werte hinzufügen")
        self.append_btn.setIcon(self.create_text_icon("+", "#4caf50"))
        self.append_btn.clicked.connect(self.on_append)
        self.append_btn.setToolTip("Fügt diese Werte am Ende der Tabelle an.")
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.append_btn)
        btn_layout.addWidget(self.replace_btn)
        
        layout.addLayout(btn_layout)
        
        self.replace_mode = False

    def on_replace(self):
        self.replace_mode = True
        self.process_import()
        
    def on_append(self):
        self.replace_mode = False
        self.process_import()

    def process_import(self):
        col_name_top = self.combo_top.currentText()
        col_name_left = self.combo_left.currentText()
        
        if col_name_top == "(Ignorieren)" or col_name_left == "(Ignorieren)":
             QMessageBox.warning(self, "Fehler", "Bitte wählen Sie für beide Achsen eine Spalte aus.")
             return

        # Parse Logic
        # Structure:
        # [0,0] [0,1: Top Value 1] [0,2: Top Value 2] ...
        # [1,0: Left Value 1] [1,1: Price] ...
        
        try:
            # Top Headers (start from col 1)
            top_values = []
            for j in range(1, len(self.rows[0])):
                val_str = self.rows[0][j].strip()
                # Clean value? Assume generic float
                top_values.append(self.clean_number(val_str))
                
            # Determine corresponding "min" column names
            col_min_top = col_name_top.replace("max", "min") if "max" in col_name_top else None
            col_min_left = col_name_left.replace("max", "min") if "max" in col_name_left else None
            
            # Pre-calculate min values for top headers (columns)
            # Assuming headers are sorted steps: 0 -> Val1 -> Val2
            # min[0] = 0, min[1] = top_values[0]
            top_mins = [0.0] + top_values[:-1]
            
            new_rows = []
            
            prev_left_val = 0.0
            
            # Iterate Data Rows (start from row 1)
            for i in range(1, len(self.rows)):
                row_data = self.rows[i]
                if not row_data: continue
                
                # Left Header (col 0)
                left_val_str = row_data[0].strip()
                left_val = self.clean_number(left_val_str)
                
                # Min value for this row (Left Dimension)
                min_left_val = prev_left_val
                
                # Iterate Cells
                for j in range(1, len(row_data)):
                    if j > len(top_values): break # Should not happen if rectangular
                    
                    price_str = row_data[j].strip()
                    if not price_str: continue
                    
                    price = self.clean_number(price_str)
                    
                    # Create Row Dict
                    # We only know X, Y and Price. Other columns (id_unit etc) will be filled with defaults or 0 by caller if missing?
                    # Caller should handle defaults. We just return partial dicts.
                    row_dict = {
                        col_name_top: top_values[j-1],
                        col_name_left: left_val,
                        "price": price
                    }
                    
                    # Add calculated min values if columns exist
                    if col_min_top and col_min_top in self.current_columns:
                        row_dict[col_min_top] = top_mins[j-1]
                        
                    if col_min_left and col_min_left in self.current_columns:
                        row_dict[col_min_left] = min_left_val
                        
                    new_rows.append(row_dict)
                
                # Update prev for next row
                prev_left_val = left_val
            
            self.result_data = new_rows
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Import Fehler", f"Fehler beim Verarbeiten:\n{str(e)}")

    def clean_number(self, val_str):
        val_str = val_str.strip()
        if not val_str: return 0.0
        
        # Regex to find the first number (integer or float with dot or comma)
        # Matches: "123", "123,45", "123.45", "1.234,56"
        # We look for digits, possibly separated by dots or commas
        # Simple approach: Extract anything that looks like a number part
        
        # 1. Normalize German format (1.000,00 -> 1000.00) vs English (1,000.00 -> 1000.00)
        # It's tricky without context, but usually copied from German Excel -> Comma is decimal.
        # Let's try to just extract the number block first.
        
        # Match anything starting with digit, then digits/dots/commas
        match = re.search(r'[0-9]+(?:[.,][0-9]+)*', val_str)
        if match:
            num_str = match.group(0)
            # Assumption: If comma is present, it's likely decimal separator in DACH region
            # OR standard US list. 
            # Heuristic: 
            # - If ',' is the last separator and looks like decimal (2 digits?), replace it with '.'
            # - Remove all other '.' (thousands)
            
            # Heuristic for thousands separators (especially German format)
            # 1. If comma AND dot present (e.g. 1.234,56): Dot is thousands, Comma is decimal.
            if ',' in num_str and '.' in num_str:
                num_str = num_str.replace('.', '').replace(',', '.')
                
            # 2. If ONLY comma (e.g. 123,45): Comma is decimal (German).
            elif ',' in num_str:
                num_str = num_str.replace(',', '.')
                
            # 3. If ONLY dot (e.g. 1.234 or 1.2): Ambiguous.
            # But in German context (Tariffs), 1.000 usually means 1000, not 1.0.
            # Check if dot is followed by exactly 3 digits (e.g. 1.000, 10.500) -> Thousands.
            elif '.' in num_str:
                # If matches pattern like 1.234 or 10.500 (dot followed by 3 digits at end or before another dot)
                # Strict check: if all dot groups have 3 digits
                parts = num_str.split('.')
                if len(parts) > 1:
                    # Check if all parts after first are 3 digits
                    # e.g. 1.000 -> ["1", "000"] -> OK -> 1000
                    # e.g. 1.5 -> ["1", "5"] -> NO -> 1.5
                    # e.g. 10.500.000 -> ["10", "500", "000"] -> OK
                    is_thousands = True
                    for p in parts[1:]:
                        if len(p) != 3:
                            is_thousands = False
                            break
                    
                    if is_thousands:
                        num_str = num_str.replace('.', '')
                    # else: leave as float (1.5 -> 1.5)
            
            try:
                return float(num_str)
            except:
                return 0.0
                
        return 0.0

    def create_text_icon(self, text, color_hex):
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setPen(QColor(color_hex))
        font = painter.font()
        font.setBold(True)
        font.setPixelSize(18)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, text)
        painter.end()
        return QIcon(pixmap)
