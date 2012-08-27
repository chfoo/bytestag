'''Shared files screen'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from PySide import QtGui, QtCore # @UnresolvedImport
from bytestagui.abstract.controllers.sharedfiles import (
    SharedFilesController as BaseSharedFilesController)
from bytestagui.abstract.views.sharedfiles import (DIRECTORY_HEADER_TEXT, 
    SCAN_PROGRESS_TEXT)
from bytestagui.qt.controllers.dht import DHTClientController
from bytestagui.qt.controllers.invoker import invoke_in_main_thread
from bytestagui.qt.controllers.loader import LoaderController
from bytestagui.qt.models.sharedfiles import SharedFilesTableModel


class SharedFilesController(BaseSharedFilesController):
    def __init__(self, application):
        BaseSharedFilesController.__init__(self, application)

        self._scan_task = None
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
        loader.connect(self._main_window.shared_files_scan_button.clicked,
            self._shared_files_scan_button_clicked_cb)
        loader.connect(self._main_window.shared_files_scan_stop_button.clicked,
            self._shared_files_scan_stop_button_clicked_cb)

        self._disable_scan_ui()
        self._create_table()

        timer = QtCore.QTimer(self.application.app)
        timer.timeout.connect(self._update_scan_progress)
        timer.start(200)

    def _create_table(self):
        table_view = self._main_window.shared_files_table_view
        tree_model = SharedFilesTableModel(
            DIRECTORY_HEADER_TEXT,
            self._shared_directories)

        table_view.setModel(tree_model)
        self._tree_model = tree_model

    def _disable_scan_ui(self):
        layout = self._main_window.shared_files_scan_layout

        for item in (layout.itemAt(i) for i in range(layout.count())):
            item.widget().hide()

        if self._scan_task:
            assert self._scan_task.is_finished

        self._scan_task = None

        self._main_window.shared_files_scan_button.setEnabled(True)

    def _enable_scan_ui(self):
        layout = self._main_window.shared_files_scan_layout

        for item in (layout.itemAt(i) for i in range(layout.count())):
            item.widget().show()

        self._main_window.shared_files_scan_button.setEnabled(False)

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

    def _shared_files_scan_button_clicked_cb(self, *args):
        self._enable_scan_ui()

        self._scan_task = self.application.singletons[
            DHTClientController].client.shared_files_table.hash_directories()

        def f(*args):
            invoke_in_main_thread(self._disable_scan_ui)

        self._scan_task.observer.register(f)

    def _shared_files_scan_stop_button_clicked_cb(self, *args):
        def f(*args):
            invoke_in_main_thread(self._disable_scan_ui)

        self._scan_task.observer.register(f)
        self._scan_task.stop()

    def _update_scan_progress(self):
        if self._scan_task:
            filename, bytes_read = self._scan_task.progress

            # FIXME: l10n support
            self._main_window.shared_files_scan_label.setText(
                SCAN_PROGRESS_TEXT.format(
                filename=filename, bytes_read=bytes_read)
            )
