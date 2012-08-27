'''Shared files qt models'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from PySide import QtCore  #@UnresolvedImport


class SharedFilesTableModel(QtCore.QAbstractTableModel):
    def __init__(self, header_text, filenames):
        QtCore.QAbstractTableModel.__init__(self)
        self._filenames = filenames
        self._header_text = header_text

    def rowCount(self, dummy):
        return len(self._filenames)

    def columnCount(self, dummy):
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
                return self._header_text

    def append(self, filename):
        index = QtCore.QModelIndex()
        position = len(self._filenames)
        rows = 1

        self.beginInsertRows(index, position, position + rows - 1)
        self._filenames.append(filename)
        self.endInsertRows()

        return True

    def remove(self, filename):
        index = QtCore.QModelIndex()
        position = self._filenames.index(filename)
        rows = 1

        self.beginRemoveRows(index, position, position + rows - 1)
        self._filenames.remove(filename)
        self.endRemoveRows()

        return True
