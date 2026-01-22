from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QComboBox, 
                               QLineEdit, QDialogButtonBox, QMessageBox)

class BulkUpdateDialog(QDialog):
    def __init__(self, engine, model, selected_rows=None, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.model = model
        self.selected_rows = selected_rows # List of row indices or None
        
        title_suffix = " (Auswahl)" if selected_rows and len(selected_rows) > 0 else " (Alle Zeilen)"
        self.setWindowTitle(f"Preisanpassung {title_suffix}")
        self.resize(300, 200)
        
        layout = QVBoxLayout(self)
        
        # Info Label
        info_label = QLabel()
        info_label.setWordWrap(True)
        # Determine text and style
        df_count = len(self.model.getDataFrame())
        if selected_rows and len(selected_rows) > 0:
            count = len(selected_rows)
            info_label.setText(f"ℹ️ Anpassung für <b>{count} ausgewählte Zeile(n)</b>.")
            info_label.setStyleSheet("color: #4caf50; font-size: 13px; font-weight: bold; margin-bottom: 10px;")
        else:
            info_label.setText(f"⚠️ Anpassung gilt für <b>ALLE {df_count} Zeile(n)</b>!")
            info_label.setStyleSheet("color: #ff9800; font-size: 13px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(info_label)

        layout.addWidget(QLabel("Spalte wählen:"))
        self.column_combo = QComboBox()
        
        # Populate columns
        df = self.model.getDataFrame()
        if not df.empty:
            self.column_combo.addItems(df.columns.tolist())
            # Default to price if available
            idx = self.column_combo.findText("price")
            if idx >= 0: self.column_combo.setCurrentIndex(idx)
            
        layout.addWidget(self.column_combo)
        
        layout.addWidget(QLabel("Änderung in % (z.B. 5.0 oder -10):"))
        self.percent_edit = QLineEdit()
        self.percent_edit.setPlaceholderText("0.0")
        layout.addWidget(self.percent_edit)
        
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.button(QDialogButtonBox.Cancel).setText("Abbrechen")
        btn_box.accepted.connect(self.apply_update)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
        
    def apply_update(self):
        col = self.column_combo.currentText()
        val_str = self.percent_edit.text()
        
        if not col:
            QMessageBox.warning(self, "Warnung", "Keine Spalte gewählt.")
            return

        try:
            pct = float(val_str)
            df = self.model.getDataFrame()
            if df.empty: return
            
            # Pass selected_rows to engine
            df = self.engine.apply_bulk_change(df, col, pct, self.selected_rows)
            self.model.setDataFrame(df)
            
            # QMessageBox.information(self, "Erfolg", f"Spalte '{col}' wurde um {pct}% angepasst.")
            self.accept()
        except ValueError:
            QMessageBox.warning(self, "Fehler", "Ungültiger Zahlenwert.")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))
