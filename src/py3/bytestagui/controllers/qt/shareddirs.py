'''Shared files screen'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from PySide import QtGui, QtCore # @UnresolvedImport
from bytestagui.controllers.base import BaseController
from bytestagui.controllers.dht import DHTClientController
from bytestagui.controllers.qt.invoker import invoke_in_main_thread
from bytestagui.controllers.qt.uiloader import UILoaderController
from bytestagui.controllers.shareddirs import SharedDirsController
from bytestagui.models.qt.shareddirs import SharedDirsTableModel
from bytestagui.views.sharedfiles import (SCAN_PROGRESS_TEXT,
    DIRECTORY_HEADER_TEXT)


class SharedDirsTableController(BaseController):
    '''Allows user to add and remove shared directories'''

    def __init__(self, application):
        BaseController.__init__(self, application)

        self._shared_dirs_controller = self.application.singletons[
            SharedDirsController]
        loader = self.application.singletons[UILoaderController]
        self._prefs_dialog = loader.preferences_dialog

        self._prefs_dialog.shared_files_remove_button.setEnabled(False)

        self._prefs_dialog.shared_files_add_button.clicked.connect(
            self._add_button_clicked_cb)
        self._prefs_dialog.shared_files_remove_button.clicked.connect(
            self._remove_button_clicked_cb)
        self._prefs_dialog.shared_files_table_view.activated.connect(
            self._table_view_activated_cb)
        self._prefs_dialog.shared_files_table_view.clicked.connect(
            self._table_view_activated_cb)

        self._create_table()

    def _create_table(self):
        table_view = self._prefs_dialog.shared_files_table_view
        tree_model = SharedDirsTableModel(DIRECTORY_HEADER_TEXT)

        table_view.setModel(tree_model)
        self._tree_model = tree_model

        for d in self._shared_dirs_controller.shared_directories:
            self._tree_model.append(d)

    def _add_button_clicked_cb(self, *args):
        dialog = QtGui.QFileDialog(self._prefs_dialog, 'Select a folder')
        dialog.setFileMode(QtGui.QFileDialog.Directory)

        if not dialog.exec_():
            return

        filenames = dialog.selectedFiles()

        for filename in filenames:
            if filename not in self._shared_dirs_controller.shared_directories:
                self._tree_model.append(filename)

        self._shared_dirs_controller.add_directory(*filenames)

    def _remove_button_clicked_cb(self, *args):
        indexes = self._prefs_dialog.shared_files_table_view.selectedIndexes()

        l = []
        for index in indexes:
            filename = self._tree_model.filenames[index.row()]

            self._tree_model.remove(filename)
            l.append(filename)

        self._shared_dirs_controller.remove_directory(*l)

    def _table_view_activated_cb(self, index):
        self._prefs_dialog.shared_files_remove_button.setEnabled(True)


class SharedDirsScanController(BaseController):
    '''Controls the scan buttons and progress label'''

    def __init__(self, application):
        BaseController.__init__(self, application)

        self._scan_task = None

        loader = self.application.singletons[UILoaderController]
        self._main_window = loader.main_window

        self._main_window.shared_files_scan_button.clicked.connect(
            self._scan_button_clicked_cb)
        self._main_window.shared_files_scan_stop_button.clicked.connect(
            self._scan_stop_button_clicked_cb)

        # FIXME: line below causes segfaults when app exits
        self._disable_scan_ui()

        timer = QtCore.QTimer(self.application.app)
        timer.timeout.connect(self._update_scan_progress)
        timer.start(200)

    def _disable_scan_ui(self):
        if self._scan_task:
            assert self._scan_task.is_finished

            self._scan_task = None

        layout = self._main_window.shared_files_scan_layout

        for item in (layout.itemAt(i) for i in range(layout.count())):
            item.widget().hide()

        self._main_window.shared_files_scan_button.setEnabled(True)

    def _enable_scan_ui(self):
        self._main_window.shared_files_scan_button.setEnabled(False)

        layout = self._main_window.shared_files_scan_layout

        for item in (layout.itemAt(i) for i in range(layout.count())):
            item.widget().show()

    def _scan_button_clicked_cb(self, *args):
        self._enable_scan_ui()

        self._scan_task = self.application.singletons[
            DHTClientController].client.shared_files_table.hash_directories()

        def f(*args):
            invoke_in_main_thread(self._disable_scan_ui)

        self._scan_task.observer.register(f)

    def _scan_stop_button_clicked_cb(self, *args):
        def f(*args):
            invoke_in_main_thread(self._disable_scan_ui)

        self._scan_task.observer.register(f)
        self._scan_task.stop()

    def _update_scan_progress(self):
        if self._scan_task and self._scan_task.progress:
            filename, bytes_read = self._scan_task.progress

            # FIXME: l10n support
            self._main_window.shared_files_scan_label.setText(
                SCAN_PROGRESS_TEXT.format(
                filename=filename, bytes_read=bytes_read)
            )
