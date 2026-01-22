from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, 
                               QPushButton, QLabel, QMessageBox, QTableWidget, 
                               QTableWidgetItem, QFormLayout, QHeaderView, 
                               QDialogButtonBox, QFileDialog)
import json

class DefinitionEditorDialog(QDialog):
    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.setWindowTitle("Tarif-Definition erstellen / bearbeiten")
        self.resize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # --- Top Toolbar ---
        top_bar = QHBoxLayout()
        load_btn = QPushButton("📂 Existierende Logik laden")
        load_btn.clicked.connect(self.load_definition_dialog)
        top_bar.addWidget(load_btn)
        top_bar.addStretch()
        layout.addLayout(top_bar)
        
        # --- Metadata Form ---
        form = QFormLayout()
        self.spec_edit = QLineEdit()
        self.desc_edit = QLineEdit()
        self.unit_edit = QLineEdit()
        self.cur_edit = QLineEdit("EUR")
        
        form.addRow("Spezifikations-Name:", self.spec_edit)
        form.addRow("Beschreibung:", self.desc_edit)
        form.addRow("Einheit (Code):", self.unit_edit)
        form.addRow("Währung:", self.cur_edit)
        
        # Connect signals for validation
        self.spec_edit.textChanged.connect(self.check_input)
        self.desc_edit.textChanged.connect(self.check_input)
        self.unit_edit.textChanged.connect(self.check_input)
        self.cur_edit.textChanged.connect(self.check_input)
        
        layout.addLayout(form)
        
        # --- Columns Table ---
        layout.addWidget(QLabel("Spalten & Standardwerte:"))
        self.col_table = QTableWidget(0, 2)
        self.col_table.setHorizontalHeaderLabels(["Spaltenname", "Standardwert"])
        self.col_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.col_table)
        
        # --- Table Actions ---
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Spalte hinzufügen")
        add_btn.clicked.connect(self.add_column_row)
        remove_btn = QPushButton("Ausgewählte entfernen")
        remove_btn.clicked.connect(self.remove_column_row)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        layout.addLayout(btn_layout)
        
        # Add some default rows for convenience
        defaults = [
            ("maxDistance", "0"), 
            ("maxWeight", "0"), 
            ("minDistance", "0"), 
            ("minWeight", "0"),
            ("price", "0"),
            ("rate", "0"),
            ("id_unit", "1"), # 9=CBM, 1=KG - Default to KG
            ("id_orderkind", "2")
        ]
        # Note: Users should manually add 'maxWeight'/'minWeight' OR 'maxVolume'/'minVolume'
        for name, val in defaults:
            self.add_column_row(name, val)
        
        # --- Dialog Buttons ---
        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Save).setText("Speichern")
        self.buttons.button(QDialogButtonBox.Cancel).setText("Abbrechen")
        self.buttons.accepted.connect(self.save_definition)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        
        # Initial check
        self.check_input()
        
    def add_column_row(self, name="", val="0"):
        row = self.col_table.rowCount()
        self.col_table.insertRow(row)
        self.col_table.setItem(row, 0, QTableWidgetItem(name))
        self.col_table.setItem(row, 1, QTableWidgetItem(val))
        
    def remove_column_row(self):
        rows = set(i.row() for i in self.col_table.selectedItems())
        for row in sorted(rows, reverse=True):
            self.col_table.removeRow(row)

    def load_definition_dialog(self):
        folder = self.engine.definitions_folder
        path, _ = QFileDialog.getOpenFileName(self, "Logik laden", folder, "JSON Files (*.json)")
        if path:
            self.load_definition(path)

    def load_definition(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Fill Metadata
            self.spec_edit.setText(data.get('spec_name', ''))
            self.desc_edit.setText(data.get('description', ''))
            self.unit_edit.setText(data.get('unit_code', ''))
            self.cur_edit.setText(data.get('currency_code', 'EUR'))
            
            # Fill Columns
            self.col_table.setRowCount(0)
            columns = data.get('columns', [])
            defaults = data.get('defaults', {})
            
            for col in columns:
                val = defaults.get(col, "0")
                self.add_column_row(col, str(val))
                
        except Exception as e:
            QMessageBox.critical(self, "Ladefehler", f"Fehler beim Laden der Datei:\n{str(e)}")

    def check_input(self):
        spec = self.spec_edit.text().strip()
        desc = self.desc_edit.text().strip()
        unit = self.unit_edit.text().strip()
        curr = self.cur_edit.text().strip()
        
        is_valid = bool(spec and desc and unit and curr)
        
        save_btn = self.buttons.button(QDialogButtonBox.Save)
        save_btn.setEnabled(is_valid)
        
        if is_valid:
            save_btn.setProperty("class", "success-btn")
        else:
             save_btn.setProperty("class", "")
             
        save_btn.style().unpolish(save_btn)
        save_btn.style().polish(save_btn)

    def save_definition(self):
        spec = self.spec_edit.text().strip()
        if not spec:
            QMessageBox.warning(self, "Fehler", "Spezifikations-Name ist erforderlich.")
            return
            
        columns = []
        defaults = {}
        
        for r in range(self.col_table.rowCount()):
            name_item = self.col_table.item(r, 0)
            val_item = self.col_table.item(r, 1)
            
            if name_item and name_item.text().strip():
                col_name = name_item.text().strip()
                columns.append(col_name)
                
                if val_item and val_item.text().strip():
                    try:
                        defaults[col_name] = float(val_item.text().strip())
                    except ValueError:
                         defaults[col_name] = val_item.text().strip()
        
        data = {
            "spec_name": spec,
            "description": self.desc_edit.text(),
            "unit_code": self.unit_edit.text(),
            "currency_code": self.cur_edit.text(),
            "id_orderkind_default": 2, # Default
            "columns": columns,
            "defaults": defaults
        }
        
        try:
            self.engine.save_definition(data, spec)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Speicherfehler", str(e))
