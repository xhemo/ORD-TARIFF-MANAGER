from PySide6.QtWidgets import QHeaderView, QDialog
from PySide6.QtCore import Qt, Signal, QSortFilterProxyModel
from PySide6.QtGui import QPainter, QColor
from .dialogs import FilterDialog

class FilterHeader(QHeaderView):
    filterChanged = Signal(int, list) # column, allowed_values

    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)
        self.setSectionsClickable(True)
        self._filters = {} # {col: set_of_values}

    def paintSection(self, painter, rect, logicalIndex):
        painter.save()
        super().paintSection(painter, rect, logicalIndex)
        painter.restore()

        # Draw Filter Icon
        if logicalIndex in self._filters:
            icon_text = "▼" # Active filter, filled
            color = QColor("#007acc") # VS Code Blue
        else:
            icon_text = "▽" # Inactive, outline (or just clean chevron)
            # Actually, standard modern UI only shows icon on hover or if filtered
            # For now, let's show a subtle chevron
            icon_text = "⌄" 
            color = QColor("#666666")
        
        # Simple text icon for now
        painter.setPen(color)
        # Adjust position slightly
        painter.drawText(rect.adjusted(0, 0, -5, 0), Qt.AlignRight | Qt.AlignVCenter, icon_text)

    def mouseReleaseEvent(self, event):
        logicalIndex = self.logicalIndexAt(event.pos())
        x_in_section = event.pos().x() - self.sectionViewportPosition(logicalIndex)
        section_width = self.sectionSize(logicalIndex)
        
        if section_width - x_in_section < 25:
            self.showFilterDialog(logicalIndex)
        else:
            super().mouseReleaseEvent(event)

    def showFilterDialog(self, col):
        model = self.model()
        if isinstance(model, QSortFilterProxyModel):
            source_model = model.sourceModel()
        else:
            source_model = model
            
        # Get unique values
        unique_values = set()
        for row in range(source_model.rowCount()):
            idx = source_model.index(row, col)
            val = source_model.data(idx, Qt.DisplayRole)
            unique_values.add(str(val))
            
        # Smart Sort
        vals_list = list(unique_values)
        try:
            sorted_values = sorted(vals_list, key=lambda x: float(x) if x and x.strip() else -float('inf'))
        except ValueError:
            sorted_values = sorted(vals_list)
        
        current_filter = self._filters.get(col, None) # Set or None
        col_name = model.headerData(col, Qt.Horizontal)
        
        dialog = FilterDialog(sorted_values, current_filter, str(col_name), self)
        if dialog.exec() == QDialog.Accepted:
            allowed = dialog.get_allowed_values()
            
            # If all selected, clear filter
            if len(allowed) == len(sorted_values):
                if col in self._filters:
                    del self._filters[col]
                self.filterChanged.emit(col, None)
            else:
                self._filters[col] = set(allowed)
                self.filterChanged.emit(col, allowed)
            
            self.viewport().update()

    def clearFilters(self):
        self._filters.clear()
        self.viewport().update()

from PySide6.QtWidgets import QTableView

class EnhancedTableView(QTableView):
    """A QTableView that clears selection when clicking on empty space."""
    def mousePressEvent(self, event):
        index = self.indexAt(event.pos())
        if not index.isValid():
            # Clear selection if clicking on empty space (and not holding Ctrl/Shift)
            if event.modifiers() == Qt.NoModifier:
                self.clearSelection()
                self.setCurrentIndex(index) 
        
        super().mousePressEvent(event)
