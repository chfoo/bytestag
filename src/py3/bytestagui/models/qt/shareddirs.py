'''Shared files qt models'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from PySide import QtCore


class SharedDirsTableModel(QtCore.QAbstractTableModel):
    def __init__(self, header_texts, filenames):
        QtCore.QAbstractTableModel.__init__(self)
        self._filenames = filenames
        self._header_texts = header_texts

    @property
    def filenames(self):
        return self._filenames

    def rowCount(self, parent_index=None):
        return len(self._filenames)

    def columnCount(self, parent_index=None):
        return 1

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return

        if not 0 <= index.row() < len(self._filenames):
            return

        if role == QtCore.Qt.DisplayRole:
            if index.column() == 0:
                return self._filenames[index.row()]

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role != QtCore.Qt.DisplayRole:
            return

        if orientation == QtCore.Qt.Horizontal:
            if section == 0:
                return self._header_texts[0]

    def insertRows(self, position, rows=1, index=QtCore.QModelIndex()):
        self.beginInsertRows(QtCore.QModelIndex(), position,
            position + rows - 1)
        self.endInsertRows()

        return True

    def removeRows(self, position, rows=1, index=QtCore.QModelIndex()):
        self.beginRemoveRows(QtCore.QModelIndex(), position,
            position + rows - 1)
        self.endRemoveRows()

        return True
