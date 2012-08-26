'''Shared files screen'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from PySide import QtGui, QtCore
from bytestagui.abstract.controllers.sharedfiles import (
    SharedFilesController as BaseSharedFilesController)
from bytestagui.qt.controllers.invoker import invoke_in_main_thread
from bytestagui.qt.controllers.loader import LoaderController


class SharedFilesTableModel(QtCore.QAbstractTableModel):
    def __init__(self, filenames):
        QtCore.QAbstractTableModel.__init__(self)
        self._filenames = filenames

    def rowCount(self, dummy):
        return len(self._filenames)

    def columnCount(self, dummy):
        return 1

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None

        if not 0 <= index.row() < len(self._filenames):
            return None

        if role == QtCore.Qt.DisplayRole:
            if index.column() == 0:
                return self._filenames[index.row()]

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role != QtCore.Qt.DisplayRole:
            return

        if orientation == QtCore.Qt.Horizontal:
            if section == 0:
                return BaseSharedFilesController.DIRECTORY_HEADER

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


class SharedFilesController(BaseSharedFilesController):
    def __init__(self, application):
        BaseSharedFilesController.__init__(self, application)

        loader = self.application.singletons[LoaderController]
        self._main_window = loader.main_window

        self._main_window.shared_files_remove_button.setEnabled(False)

        loader.connect(self._main_window.shared_files_add_button.clicked,
            self._shared_files_add_button_clicked_cb)
        loader.connect(self._main_window.shared_files_remove_button.clicked,
            self._shared_files_remove_button_clicked_cb)
        loader.connect(self._main_window.shared_files_table_view.activated,
            self._shared_files_table_view_activated_cb)
        loader.connect(self._main_window.shared_files_table_view.clicked,
            self._shared_files_table_view_activated_cb)

        self._disable_scan_ui()
        self._create_tree_view_columns()

    def _create_tree_view_columns(self):
        table_view = self._main_window.shared_files_table_view
        tree_model = SharedFilesTableModel(self._shared_directories)

        table_view.setModel(tree_model)
        self._tree_model = tree_model

    def _disable_scan_ui(self):
        layout = self._main_window.shared_files_scan_layout

        for item in (layout.itemAt(i) for i in range(layout.count())):
            item.widget().hide()

    def _enable_scan_ui(self):
        layout = self._main_window.shared_files_scan_layout

        for item in (layout.itemAt(i) for i in range(layout.count())):
            item.widget().show()

    def _shared_files_add_button_clicked_cb(self, *args):
        dialog = QtGui.QFileDialog(self._main_window)
        dialog.setFileMode(QtGui.QFileDialog.Directory)

        if dialog.exec_():
            filenames = dialog.selectedFiles()

            for filename in filenames:
                if filename not in self._shared_directories:
                    self._tree_model.append(filename)

        self._save_shared_files_config()

    def _shared_files_remove_button_clicked_cb(self, *args):
        indexes = self._main_window.shared_files_table_view.selectedIndexes()

        for index in indexes:
            filename = self._shared_directories[index.row()]

            self._tree_model.remove(filename)

        self._save_shared_files_config()

    def _shared_files_table_view_activated_cb(self, index):
        self._main_window.shared_files_remove_button.setEnabled(True)
