from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLineEdit, QCheckBox, 
                               QScrollArea, QDialogButtonBox, QWidget, QDialog)
from PySide6.QtCore import Qt

class FilterDialog(QDialog):
    def __init__(self, sorted_values, active_filters, col_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Filter: {col_name}")
        self.resize(300, 400)
        
        self.values = sorted_values
        self.active_filters = active_filters # set or None
        
        # Check if all selected (no filter active means all selected)
        is_all_selected = (self.active_filters is None) or (len(self.active_filters) == len(self.values))
        if self.active_filters is None:
            self.active_filters = set(self.values)

        layout = QVBoxLayout(self)
        
        # Search
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Suchen...")
        self.search_edit.textChanged.connect(self.filter_list)
        layout.addWidget(self.search_edit)
        
        # Select All
        self.cb_all = QCheckBox("(Alles auswählen)")
        self.cb_all.setChecked(is_all_selected)
        self.cb_all.stateChanged.connect(self.toggle_all)
        layout.addWidget(self.cb_all)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self.scroll_layout = QVBoxLayout(content)
        self.scroll_layout.setContentsMargins(0,0,0,0)
        self.scroll_layout.setSpacing(2)
        
        self.checkboxes = [] # (val, QCheckBox)
        
        for val in self.values:
            cb = QCheckBox(val)
            is_checked = val in self.active_filters
            cb.setChecked(is_checked)
            self.scroll_layout.addWidget(cb)
            self.checkboxes.append((val, cb))
            
        self.scroll_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        # Buttons
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.button(QDialogButtonBox.Cancel).setText("Abbrechen")
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def filter_list(self, text):
        text = text.lower()
        visible_any = False
        for val, cb in self.checkboxes:
            if text in val.lower():
                cb.show()
                visible_any = True
            else:
                cb.hide()
                
    def toggle_all(self, state):
        # Only toggle visible items if search is active? 
        # For Excel-like consistency, toggle all usually toggles all visible. 
        # Simplified: toggle all.
        is_checked = (state == Qt.Checked)
        text = self.search_edit.text().lower()
        
        for val, cb in self.checkboxes:
            if not text or text in val.lower():
                cb.setChecked(is_checked)

    def get_allowed_values(self):
        allowed = []
        for val, cb in self.checkboxes:
            if cb.isChecked():
                allowed.append(val)
        return allowed
