'''Transfer qt models'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from PySide import QtCore
from bytestag.dht.network import StoreToNodeTask


class TransfersTableModel(QtCore.QAbstractTableModel):
    def __init__(self, header_texts):
        QtCore.QAbstractTableModel.__init__(self)
        self._header_texts = header_texts
        self._tasks = []

    def rowCount(self, parent_index=None):
        return len(self._tasks)

    def columnCount(self, parent_index=None):
        return 4

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role != QtCore.Qt.DisplayRole:
            return

        if orientation == QtCore.Qt.Horizontal:
            if 0 <= section < len(self._header_texts):
                return self._header_texts[section]

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return

        if not 0 <= index.row() < len(self._tasks):
            return

        if role == QtCore.Qt.DisplayRole:
            task = self._tasks[index.row()]
            col = index.column()

            if col == 0:
                # FIXME: use real icons
                if isinstance(task, StoreToNodeTask):
                    return '↑'
                else:  # ReadStoreFromNodeTask
                    return '↓'

            elif col == 1:
                if not hasattr(task, 'address') or not task.address:
                    return ''

                return '{} {}'.format(*task.address)
            elif col == 2:
                if not task.key:
                    return ''

                return '{}:{}'.format(task.key.base32, task.index.base32)
            elif col == 3:
                # FIXME: this should be a progress bar
                if not task.progress:
                    return 0.0

                return task.progress / task.total_size

    def append(self, task):
        index = QtCore.QModelIndex()
        position = len(self._tasks)
        rows = 1

        self.beginInsertRows(index, position, position + rows - 1)
        self._tasks.append(task)
        self.endInsertRows()

        return True

    def remove(self, task):
        index = QtCore.QModelIndex()
        position = self._tasks.index(task)
        rows = 1

        self.beginRemoveRows(index, position, position + rows - 1)
        self._tasks.remove(task)
        self.endRemoveRows()

        return True

    def emit_data_changed(self):
        self.emit(QtCore.SIGNAL('dataChanged()'))
