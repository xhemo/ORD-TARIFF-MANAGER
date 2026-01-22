import pandas as pd
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QSortFilterProxyModel

class FilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filters = {}  # {column_index: set_of_allowed_values}

    def setFilterByColumn(self, column, allowed_values):
        if allowed_values is None:
            if column in self.filters:
                del self.filters[column]
        else:
            self.filters[column] = set(str(v) for v in allowed_values)
        self.invalidateFilter()

    def clearFilters(self):
        self.filters.clear()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        if not self.filters:
            return True
            
        model = self.sourceModel()
        for col, allowed in self.filters.items():
            index = model.index(source_row, col, source_parent)
            data = model.data(index, Qt.DisplayRole)
            if str(data) not in allowed:
                return False
        return True

class PandasModel(QAbstractTableModel):
    def __init__(self, df=pd.DataFrame()):
        super().__init__()
        self._df = df

    def rowCount(self, parent=QModelIndex()):
        return self._df.shape[0]

    def columnCount(self, parent=QModelIndex()):
        return self._df.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            # Check bounds just in case
            if index.row() >= self._df.shape[0] or index.column() >= self._df.shape[1]:
                return None
                
            value = self._df.iloc[index.row(), index.column()]
            if isinstance(value, float):
                # If it has no decimal part, show as int
                if value.is_integer():
                    return str(int(value))
                return f"{value:.2f}"
            return str(value)
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if section < len(self._df.columns):
                    return self._df.columns[section]
            if orientation == Qt.Vertical:
                return str(section + 1)
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            try:
                # Attempt to convert to float if column is numeric
                current_val = self._df.iloc[index.row(), index.column()]
                if isinstance(current_val, (float, int)):
                    val = float(value)
                else:
                    val = value
                
                self._df.iloc[index.row(), index.column()] = val
                self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
                return True
            except ValueError:
                return False
        return False
    
    def setDataFrame(self, df):
        self.beginResetModel()
        self._df = df
        self.endResetModel()

    def getDataFrame(self):
        return self._df
