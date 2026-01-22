import os
import pandas as pd
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QTableView, QPushButton, QLabel, QLineEdit, QComboBox, 
                               QDockWidget, QFrame, QFileDialog, QMessageBox, QDialog, 
                               QDialogButtonBox, QRadioButton, QButtonGroup, QDateEdit, QHeaderView, QApplication)
from PySide6.QtCore import Qt, QDate, QSize, QTimer, QEvent
from PySide6.QtGui import QColor, QPalette, QIcon, QPixmap, QPainter, QFont

# Adjust import based on sys.path setup in main.py
from core.tariff_engine import TariffEngine

from .models import PandasModel, FilterProxyModel
from .widgets import FilterHeader, EnhancedTableView
from .dialogs import BulkUpdateDialog, MatrixImportDialog, DefinitionEditorDialog

from core.utils import get_resource_path

def load_stylesheet():
    """Load the QSS styles from the file."""
    try:
        # Looking for src/ui/styles.qss. 
        # In dev: project_root/src/ui/styles.qss
        # In build: we will likely place it at root level or maintain structure.
        # Let's assume we map it to "src/ui/styles.qss" in build spec too, or just "styles.qss" at root?
        # Simpler: Let's assume we bundle 'src/ui/styles.qss' relative to root.
        style_path = get_resource_path(os.path.join('src', 'ui', 'styles.qss'))
        
        # Fallback if that fails (e.g. if we flattened it in build)
        if not os.path.exists(style_path):
             style_path = get_resource_path('styles.qss')
             
        if os.path.exists(style_path):
            with open(style_path, 'r') as f:
                return f.read()
    except Exception as e:
        print(f"Error loading stylesheet: {e}")
    return ""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ORD Tariff Manager")
        self.setWindowTitle("ORD Tariff Manager")
        self.first_show = True
        
        self.engine = TariffEngine()
        
        # Use centralized path logic
        self.template_folder = get_resource_path("XML Vorlage")
        
        # Load Modern Stylesheet
        qss = load_stylesheet()
        if qss:
            # Apply to entire application so dialogs pick it up
            QApplication.instance().setStyleSheet(qss)
        
        # --- Central Widget (Table) ---
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        self.table_view = EnhancedTableView()
        self.model = PandasModel()
        
        # Setup Proxy Model for Filtering
        self.proxy_model = FilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.table_view.setModel(self.proxy_model)
        
        # Setup Custom Filter Header
        self.header = FilterHeader(self.table_view)
        self.header.setSectionResizeMode(QHeaderView.Stretch)
        self.header.filterChanged.connect(self.proxy_model.setFilterByColumn)
        self.table_view.setHorizontalHeader(self.header)
        
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.ExtendedSelection)
        self.main_layout.addWidget(self.table_view)

        # Monitor selection changes
        self.table_view.selectionModel().selectionChanged.connect(self.update_delete_button_state)

        # --- Sidebar (Templates) ---
        self.dock = QDockWidget("Templates", self)
        self.dock.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.dock.setTitleBarWidget(QWidget()) # Hide title bar
        self.dock_widget = QWidget()
        self.dock_widget.setObjectName("dock_container") # For QSS styling
        self.dock_layout = QVBoxLayout(self.dock_widget)
        self.dock_layout.setContentsMargins(0, 10, 0, 0)
        self.dock_layout.setSpacing(2) # Tight list spacing
        
        # Open File Button
        open_btn = QPushButton("📂  XML Tarif öffnen")
        open_btn.clicked.connect(self.open_xml_file)
        open_btn.setProperty("class", "sidebar-btn")
        open_btn.setCursor(Qt.PointingHandCursor)
        self.dock_layout.addWidget(open_btn)

        # Create New Button
        create_btn = QPushButton("  Neuen XML Tarif erstellen")
        create_btn.setIcon(self.create_text_icon("+", "#4caf50"))
        create_btn.clicked.connect(self.create_new_tariff)
        create_btn.setProperty("class", "sidebar-btn")
        create_btn.setCursor(Qt.PointingHandCursor)
        self.dock_layout.addWidget(create_btn)
        
        # New Definition Button
        def_btn = QPushButton("🛠  Tariflogik Manager")
        def_btn.clicked.connect(self.open_definition_editor)
        def_btn.setProperty("class", "sidebar-btn")
        def_btn.setCursor(Qt.PointingHandCursor)
        self.dock_layout.addWidget(def_btn)

        # Templates section removed as requested
        
        self.dock_layout.addStretch()

        # --- Footer ---
        footer_widget = QWidget()
        footer_widget.setObjectName("sidebar_footer") # Make transparent in QSS
        footer_layout = QVBoxLayout(footer_widget)
        footer_layout.setContentsMargins(10, 0, 10, 10)
        footer_layout.setSpacing(5)

        # Info Area (Permanent)
        
        # Expandable Info Area
        self.info_content = QLabel(
            "© 2026 Xhemajl Dvorani\n"
            "Alle Rechte vorbehalten.\n"
            "Diese Software ist privates\n"
            "geistiges Eigentum des Urhebers.\n"
            "Bereitstellung erfolgt unter Nutzungslizenz.\n"
            "Kein Eigentumsübertrag.\n"
            "Lizenz jederzeit ohne Vorankündigung widerrufbar."
        )
        # Allow multi-line text
        self.info_content.setWordWrap(True)
        self.info_content.setObjectName("info_content")
        self.info_content.setVisible(True) # Always visible
        
        footer_layout.addWidget(self.info_content)
        
        self.dock_layout.addWidget(footer_widget)
        self.dock.setWidget(self.dock_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock)
        
        # Default width handled in showEvent
        
        # --- Top Header (Metadata) ---
        self.header_frame = QFrame()
        self.header_frame.setObjectName("header_frame")
        self.header_layout = QHBoxLayout(self.header_frame)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Tarifname")
        self.header_layout.addWidget(QLabel("Name:"))
        self.header_layout.addWidget(self.name_edit)
        
        self.valid_from = QDateEdit()
        self.valid_from.setCalendarPopup(True)
        self.valid_from.setDisplayFormat("dd.MM.yyyy")
        self.valid_from.setDate(QDate.currentDate())
        self.header_layout.addWidget(QLabel("Gültig ab:"))
        self.header_layout.addWidget(self.valid_from)
        
        self.valid_to = QDateEdit()
        self.valid_to.setCalendarPopup(True)
        self.valid_to.setDisplayFormat("dd.MM.yyyy")
        self.valid_to.setDate(QDate(2099, 12, 31))
        self.header_layout.addWidget(QLabel("Gültig bis:"))
        self.header_layout.addWidget(self.valid_to)

        self.kind_combo = QComboBox()
        self.kind_combo.addItems(["Distribution", "Return"])
        self.kind_combo.currentTextChanged.connect(self.update_order_kind_in_table)
        self.header_layout.addWidget(QLabel("Auftragsart:"))
        self.header_layout.addWidget(self.kind_combo)
        
        self.header_layout.addWidget(QLabel("Spezifikation:"))
        self.spec_label = QLineEdit()
        self.spec_label.setReadOnly(True) 
        self.spec_label.setPlaceholderText("Tarif-Spezifikation")
        self.header_layout.addWidget(self.spec_label)

        # Header inputs are enabled by default (User request)

        self.main_layout.insertWidget(0, self.header_frame)

        # --- Table Toolbar (Row Actions & Filters) ---
        self.toolbar_frame = QFrame()
        self.toolbar_frame.setObjectName("toolbar_frame")
        self.toolbar_layout = QHBoxLayout(self.toolbar_frame)
        self.toolbar_layout.setContentsMargins(0, 5, 0, 5)

        
        # Row Actions
        add_row_btn = QPushButton(" Zeile hinzufügen")
        add_row_btn.setIcon(self.create_text_icon("+", "#4caf50")) # Green Plus
        add_row_btn.clicked.connect(self.add_row)
        add_row_btn.setObjectName("btn_add_row")
        self.toolbar_layout.addWidget(add_row_btn)
        
        self.del_row_btn = QPushButton(" Alle Zeilen löschen")
        self.del_row_btn.setIcon(self.create_text_icon("-", "#ef5350")) # Red Minus
        self.del_row_btn.clicked.connect(self.delete_rows_action)
        self.del_row_btn.setObjectName("btn_del_row")
        self.toolbar_layout.addWidget(self.del_row_btn)
        
        # Spacer
        self.toolbar_layout.addStretch()

        # Clear Filters
        clear_filter_btn = QPushButton("✖ Filter zurücksetzen")
        clear_filter_btn.clicked.connect(self.clear_all_filters)
        self.toolbar_layout.addWidget(clear_filter_btn)
        
        self.main_layout.addWidget(self.toolbar_frame)

        # --- Placeholder Widget (Empty State) ---
        self.placeholder_widget = QWidget()
        placeholder_layout = QVBoxLayout(self.placeholder_widget)
        
        # Use simple spacers for optical centering (approx 1/3 down)
        placeholder_layout.addStretch() # Equal stretch above
        
        placeholder_label = QLabel(
            "<h2 style='color: #666; font-family: sans-serif;'>Willkommen im ORD Tariff Manager</h2>"
            "<p style='color: #888; font-size: 14px;'>Bitte erstelle einen <b>neuen Tarif</b> oder öffne einen <b>bestehenden</b>.<br>"
            "Nutze dazu die Schaltflächen in der linken Seitenleiste.</p>"
        )
        placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_layout.addWidget(placeholder_label)
        
        placeholder_layout.addStretch() # Equal stretch below
        
        self.main_layout.addWidget(self.placeholder_widget)

        # --- Bottom Action Bar ---
        self.action_frame = QFrame()
        self.action_frame.setObjectName("action_frame")
        self.action_layout = QHBoxLayout(self.action_frame)
        
        # Zwischenablage (was Matrix Import)
        matrix_btn = QPushButton("📋 Aus Zwischenablage einfügen")
        matrix_btn.clicked.connect(self.open_matrix_import)
        matrix_btn.setProperty("class", "primary-btn") 
        self.action_layout.addWidget(matrix_btn)

        # Bulk Update Button
        bulk_btn = QPushButton("📉 %-Anpassung")
        bulk_btn.clicked.connect(self.open_bulk_update_dialog)
        self.action_layout.addWidget(bulk_btn)

        # Spacer to push Generate to the right
        self.action_layout.addStretch()

        # Generate XML
        gen_btn = QPushButton("💾 XML generieren")
        gen_btn.clicked.connect(self.generate_xml)
        gen_btn.setProperty("class", "success-btn")
        gen_btn.setCursor(Qt.PointingHandCursor)
        self.action_layout.addWidget(gen_btn)

        self.main_layout.addWidget(self.action_frame)
        
        # Install Event Filters for Click-to-Deselect
        # This catches clicks on the container backgrounds
        self.central_widget.installEventFilter(self)
        self.dock_widget.installEventFilter(self)
        self.dock.installEventFilter(self) 
        self.header_frame.installEventFilter(self)
        self.toolbar_frame.installEventFilter(self)
        self.action_frame.installEventFilter(self)

        # Ensure no selection or clear model initially
        self.model.setDataFrame(pd.DataFrame()) # Empty start
        self.update_ui_state() # Initial state check

    def update_ui_state(self):
        """Toggles between Placeholder and Table View based on data existence."""
        df = self.model.getDataFrame()
        # has_data = df is not None and not df.empty
        # Modified so that empty tables (but with Schema/Columns) are also shown!
        has_data = df is not None and len(df.columns) > 0
        
        if has_data:
            self.placeholder_widget.hide()
            self.table_view.show()
            self.toolbar_frame.show()
            self.action_frame.show()
        else:
            self.placeholder_widget.show()
            self.table_view.hide()
            self.toolbar_frame.hide()
            # Maybe keep action frame hidden too if no data?
            # User workflow: Load/Create -> Data appears -> Actions enabled.
            # So hiding actions makes sense.
            self.action_frame.hide()

    def open_xml_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "XML Datei öffnen", self.template_folder, "XML Files (*.xml)")
        if file_path:
            self._load_file(file_path)

    def _load_file(self, path):
        if not os.path.exists(path):
            return

        success, msg = self.engine.load_template(path)
        if not success:
            QMessageBox.critical(self, "Error", msg)
            return
            
        # Load Metadata
        meta = self.engine.get_metadata()
        self.name_edit.setText(meta.get('name', ''))
        self.spec_label.setText(meta.get('spec', ''))
        
        # Parse Dates
        try:
            vf = QDate.fromString(meta.get('valid_from', ''), "yyyy-MM-dd")
            if vf.isValid(): self.valid_from.setDate(vf)
            
            vt = QDate.fromString(meta.get('valid_to', ''), "yyyy-MM-dd")
            if vt.isValid(): self.valid_to.setDate(vt)
        except:
            pass # Keep default if parse fails
        
        # Load Data
        result = self.engine.extract_tuples_check_schema()
        df = pd.DataFrame(result['data'])
        self.model.setDataFrame(df)
        self.update_ui_state()
        
        # Auto-detect Order Kind
        if 'id_orderkind' in df.columns and not df.empty:
            # Get first value
            try:
                kind_val = int(float(df['id_orderkind'].iloc[0]))
                if kind_val == 2:
                    index = self.kind_combo.findText("Distribution")
                    if index >= 0: self.kind_combo.setCurrentIndex(index)
                elif kind_val == 3:
                    index = self.kind_combo.findText("Return")
                    if index >= 0: self.kind_combo.setCurrentIndex(index)
            except (ValueError, IndexError):
                pass
        
        # Connect signal after loading to avoid overwriting data with default combo value
        try:
             self.kind_combo.currentTextChanged.disconnect()
        except:
             pass
        self.kind_combo.currentTextChanged.connect(self.update_order_kind_in_table)

    def update_order_kind_in_table(self):
        kind_str = self.kind_combo.currentText()
        if not kind_str: return
        
        val = 2 if kind_str == "Distribution" else 3
        
        # Since using Proxy Model, we must be careful. 
        # Easier to update source model directly.
        df = self.model.getDataFrame()
        if not df is None and not df.empty and 'id_orderkind' in df.columns:
            df['id_orderkind'] = val
            self.model.setDataFrame(df)

    def open_bulk_update_dialog(self):
        df = self.model.getDataFrame()
        if df.empty:
            QMessageBox.warning(self, "Info", "Tabelle ist leer. Bitte laden Sie zuerst einen Tarif.")
            return
            
        # Get selected rows
        selection = self.table_view.selectionModel()
        selected_rows = []
        if selection.hasSelection():
            proxy_indexes = selection.selectedRows()
            selected_rows = [self.proxy_model.mapToSource(idx).row() for idx in proxy_indexes]
            
        dialog = BulkUpdateDialog(self.engine, self.model, selected_rows, self)
        dialog.exec()

    def add_row(self):
        df = self.model.getDataFrame()
        
        # Get defaults
        defaults = self.engine.get_parameter_defaults()
        
        if df.empty:
            # If dataframe is empty, create a new one with default columns
            current_schema = self.engine.get_current_schema()
            if not current_schema:
                QMessageBox.warning(self, "Warnung", "Kein Schema verfügbar, um eine neue Zeile zu erstellen. Bitte laden Sie zuerst einen Tarif oder erstellen Sie einen neuen.")
                return
            
            # Use defaults or fallback to ""
            new_row_data = {}
            for col in current_schema:
                new_row_data[col] = defaults.get(col, "")
                
            new_df = pd.DataFrame([new_row_data])
            self.model.setDataFrame(new_df)
            self.update_ui_state()
        else:
            # Create a new row with the same columns as the existing DataFrame
            new_row_data = {}
            for col in df.columns:
                # 1. Try engine defaults
                if col in defaults:
                    new_row_data[col] = defaults[col]
                # 2. Try to infer from existing data (if previous rows exist)
                elif len(df) > 0 and pd.api.types.is_numeric_dtype(df[col]):
                    new_row_data[col] = 0.0
                # 3. Fallback
                else:
                    new_row_data[col] = ""
                    
            new_row_df = pd.DataFrame([new_row_data])
            df = pd.concat([df, new_row_df], ignore_index=True)
            self.model.setDataFrame(df)

    def open_matrix_import(self):
        # Get current column names
        df = self.model.getDataFrame()
        
        # Check if Schema exists (Columns) rather than data (Rows)
        if df is None or len(df.columns) == 0:
            QMessageBox.warning(self, "Fehler", "Bitte erstelle erst einen neuen oder öffne einen bestehenden Tarif.")
            return
            
        cols = df.columns.tolist()
        dialog = MatrixImportDialog(cols, self)
        if dialog.exec() == QDialog.Accepted:
            new_data = dialog.result_data
            if not new_data: return
            
            # Convert to DataFrame
            new_df = pd.DataFrame(new_data)
            
            # Merge with existing schema
            
            # Fetch defaults from engine
            defaults = self.engine.get_parameter_defaults()
            
            # Additional Context: Order Kind
            try:
                 kind_str = self.kind_combo.currentText()
                 selected_kind = 2 if kind_str == "Distribution" else 3
            except:
                 selected_kind = 0

            # Ensure new_df has all columns of 'df'
            for col in df.columns:
                if col not in new_df.columns:
                    # 1. Check for specific overrides first
                    if col == 'id_orderkind':
                        val = selected_kind
                    # 2. Check defaults from definition
                    elif col in defaults:
                        val = defaults[col]
                    # 3. Fallback (try existing row or 0)
                    else:
                        val = df.iloc[0][col] if not df.empty else 0
                    
                    new_df[col] = val
                    
            # Concat
            
            # Check if we should Replace or Append (Based on Dialog Selection)
            # If dialog.replace_mode is True, we clear existing data first
            if getattr(dialog, 'replace_mode', False):
                 df = pd.DataFrame(columns=df.columns) # Clear but keep schema
            
            combined_df = pd.concat([df, new_df], ignore_index=True)
            self.model.setDataFrame(combined_df)
            # QMessageBox.information(self, "Import", f"{len(new_data)} Zeilen importiert.")

    def update_delete_button_state(self):
        selection = self.table_view.selectionModel()
        if selection.hasSelection():
            self.del_row_btn.setText(" Ausgewählte Zeilen löschen")
        else:
            self.del_row_btn.setText(" Alle Zeilen löschen")

    def delete_rows_action(self):
        selection = self.table_view.selectionModel()
        df = self.model.getDataFrame()
        
        if df.empty:
             return

        if not selection.hasSelection():
            # Delete ALL rows
            confirm = QMessageBox.critical(self, "Löschen bestätigen", 
                                           "Möchten Sie wirklich ALLE Zeilen löschen?", 
                                           QMessageBox.Yes | QMessageBox.No)
            if confirm == QMessageBox.Yes:
                # Clear DataFrame but keep columns
                empty_df = pd.DataFrame(columns=df.columns)
                # Clear DataFrame but keep columns
                empty_df = pd.DataFrame(columns=df.columns)
                self.model.setDataFrame(empty_df)
                self.update_ui_state()
        else:
            # Delete SELECTED rows
            proxy_indexes = selection.selectedRows()
            source_indexes = [self.proxy_model.mapToSource(idx).row() for idx in proxy_indexes]
            rows = set(source_indexes)
            
            if not rows: return

            confirm = QMessageBox.critical(self, "Löschen bestätigen", 
                                           f"Möchten Sie wirklich {len(rows)} ausgewählte Zeile(n) löschen?", 
                                           QMessageBox.Yes | QMessageBox.No)
            
            if confirm == QMessageBox.Yes:
                df = df.drop(list(rows))
                df = df.reset_index(drop=True)
                self.model.setDataFrame(df)
                # Clear selection after delete to reset button text
                self.table_view.clearSelection()

    def clear_all_filters(self):
        self.proxy_model.clearFilters()
        self.header.clearFilters()

    def generate_xml(self):
        try:
            # 1. Update Metadata
            new_meta = {
                'name': self.name_edit.text(),
                'valid_from': self.valid_from.date().toString("yyyy-MM-dd"),
                'valid_to': self.valid_to.date().toString("yyyy-MM-dd"),
                'id': self.name_edit.text()
            }
            self.engine.update_metadata(new_meta)

            # 2. Update Order Kind
            df = self.model.getDataFrame()
            kind_str = self.kind_combo.currentText()
            if kind_str == "Auslieferung":
                df = self.engine.set_order_kind(df, 2)
            elif kind_str == "Retoure":
                df = self.engine.set_order_kind(df, 3)

            # 3. Update XML
            self.engine.update_tuples(df)

            # 4. Save
            default_name = self.name_edit.text() + ".xml"
            save_path, _ = QFileDialog.getSaveFileName(self, "XML speichern", default_name, "XML Files (*.xml)")
            if save_path:
                self.engine.save_to_file(save_path)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Ein Fehler ist aufgetreten:\n{str(e)}")
            import traceback
            traceback.print_exc() # Print to console/terminal as well

    def create_new_tariff(self):
        # Dialog to choose Definition and Order Kind
        dialog = QDialog(self)
        dialog.setWindowTitle("Neuen Tarif erstellen")
        dialog.setFixedWidth(350)
        layout = QVBoxLayout(dialog)
        
        # 0. Name Input (Mandatory)
        layout.addWidget(QLabel("Tarif Name:"))
        name_input = QLineEdit()
        name_input.setPlaceholderText("z.B. VELUX_LEJ_DISTRI_2025")
        layout.addWidget(name_input)
        
        # 1. Logic Selection
        layout.addWidget(QLabel("Tarif-Logik wählen:"))
        logic_combo = QComboBox()
        definitions = self.engine.get_available_definitions()
        logic_combo.addItems(definitions)
        layout.addWidget(logic_combo)
        
        # 2. Order Kind Selection
        layout.addWidget(QLabel("Auftragsart wählen:"))
        kind_group = QButtonGroup(dialog)
        
        radio_delivery = QRadioButton("Distribution")
        radio_delivery.setChecked(True)
        kind_group.addButton(radio_delivery, 2)
        layout.addWidget(radio_delivery)
        
        radio_return = QRadioButton("Return")
        kind_group.addButton(radio_return, 3)
        layout.addWidget(radio_return)
        
        # 3. Validity Dates
        layout.addWidget(QLabel("Gültig von:"))
        valid_from_edit = QDateEdit()
        valid_from_edit.setCalendarPopup(True)
        valid_from_edit.setDate(QDate.currentDate())
        valid_from_edit.setDisplayFormat("dd.MM.yyyy")
        layout.addWidget(valid_from_edit)
        
        layout.addWidget(QLabel("Gültig bis:"))
        valid_to_edit = QDateEdit()
        valid_to_edit.setCalendarPopup(True)
        valid_to_edit.setDate(QDate(2099, 12, 31))
        valid_to_edit.setDisplayFormat("dd.MM.yyyy")
        layout.addWidget(valid_to_edit)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, dialog)
        buttons.button(QDialogButtonBox.Cancel).setText("Abbrechen")
        
        # Customize OK Button
        ok_btn = buttons.button(QDialogButtonBox.Ok)
        ok_btn.setText("Erstellen")
        # ok_btn.setProperty("class", "success-btn") # Green style - Set dynamically now
        ok_btn.setEnabled(False) # Disabled initially
        
        def check_input():
            is_valid = bool(name_input.text().strip())
            ok_btn.setEnabled(is_valid)
            if is_valid:
                ok_btn.setProperty("class", "success-btn")
            else:
                ok_btn.setProperty("class", "")
            
            ok_btn.style().unpolish(ok_btn)
            ok_btn.style().polish(ok_btn)
            
        name_input.textChanged.connect(check_input)

        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.Accepted:
            tariff_name = name_input.text().strip()
            selected_def = logic_combo.currentText()
            selected_kind = kind_group.checkedId()
            date_from = valid_from_edit.date()
            date_to = valid_to_edit.date()
            
            if not selected_def:
                return

            try:
                # Create from definition
                result = self.engine.create_from_definition(selected_def)
                df = result['data']
                
                # Apply Order Kind to DataFrame
                if 'id_orderkind' in df.columns:
                    df['id_orderkind'] = selected_kind
                
                # Update GUI
                self.model.setDataFrame(df)
                self.update_ui_state()
                
                # Update Header UI to match selection
                if selected_kind == 2:
                    index = self.kind_combo.findText("Distribution")
                    if index >= 0: self.kind_combo.setCurrentIndex(index)
                else:
                    index = self.kind_combo.findText("Return")
                    if index >= 0: self.kind_combo.setCurrentIndex(index)
                
                # Update Metadata fields
                self.name_edit.setText(tariff_name)
                self.spec_label.setText(selected_def.replace(".json", "")) # Show clean name
                self.valid_from.setDate(date_from)
                self.valid_to.setDate(date_to)
                
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Fehler beim Erstellen des Tarifs: {str(e)}")

    def open_definition_editor(self):
        dialog = DefinitionEditorDialog(self.engine, self)
        if dialog.exec() == QDialog.Accepted:
            pass

    def showEvent(self, event):
        super().showEvent(event)
        if self.first_show:
            self.resizeDocks([self.dock], [250], Qt.Horizontal)
            self.first_show = False

    def eventFilter(self, source, event):
        if event.type() == QEvent.MouseButtonPress:
            # Check if the click is on one of our background containers
            # source is the object receiving the event
            # We want to clear selection if the user clicks on the background of these frames
            if source in (self.central_widget, self.dock_widget, self.header_frame, self.toolbar_frame, self.action_frame, self.dock):
                 if hasattr(self, 'table_view'):
                     self.table_view.clearSelection()
                     self.table_view.setCurrentIndex(self.table_view.rootIndex())
        return super().eventFilter(source, event)

    def mousePressEvent(self, event):
        # Deselect items if clicking on main window background
        child = self.childAt(event.pos())
        if child is None or child == self.central_widget:
             if hasattr(self, 'table_view'):
                 self.table_view.clearSelection()
                 self.table_view.setCurrentIndex(self.table_view.rootIndex())
        super().mousePressEvent(event)

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
