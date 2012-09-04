'''Transfer screen'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from PySide import QtCore, QtGui # @UnresolvedImport
from bytestag.dht.network import (ReadStoreFromNodeTask, StoreToNodeTask, 
    StoreValueTask)
from bytestagui.controllers.base import BaseController
from bytestagui.controllers.dht import DHTClientController
from bytestagui.controllers.qt.invoker import invoke_in_main_thread
from bytestagui.controllers.qt.uiloader import UILoaderController
from bytestagui.models.qt.transfers import TransfersTableModel
from bytestagui.views.transfers import TABLE_HEADER_TEXTS


class TransfersTableController(BaseController):
    def __init__(self, application):
        BaseController.__init__(self, application)

        loader = self.application.singletons[UILoaderController]
        self._main_window = loader.main_window

        self._create_table()
        self._connect_download_slot()
        self._connect_upload_slot()

        timer = QtCore.QTimer(self.application.app)
        timer.timeout.connect(self._update_table)
        timer.start(200)

    def _create_table(self):
        table_view = self._main_window.transfers_table_view
        tree_model = TransfersTableModel(TABLE_HEADER_TEXTS)

        table_view.setModel(tree_model)
        self._tree_model = tree_model

        # TODO: figure out how to use progress bars in item views
#        self._progress_bars = []
#
#        for i in range(100):
#            index = self._tree_model.createIndex(i, 3)
#            progress_bar = QtGui.QProgressBar()
#
#            progress_bar.minimum = 0
#            progress_bar.maximum = 1
#            self._progress_bars.append(progress_bar)
#            table_view.setIndexWidget(index, progress_bar)

    def _update_table(self):
        self._tree_model.emit_data_changed()

    def _connect_upload_slot(self):
        upload_slot = self.application.singletons[DHTClientController
            ].client.upload_slot

        def store_to_node_task_cb(added, task):
            assert isinstance(task, StoreToNodeTask)

            if added:
                invoke_in_main_thread(self._tree_model.append, task)
            else:
                invoke_in_main_thread(self._tree_model.remove, task)

        def upload_slot_callback(added, task):
            assert isinstance(task, StoreValueTask)

            task.store_to_node_task_observer.register(store_to_node_task_cb)

        upload_slot.observer.register(upload_slot_callback)

    def _connect_download_slot(self):
        download_slot = self.application.singletons[DHTClientController
            ].client.download_slot

        def download_slot_callback(added, task):
            assert isinstance(task, ReadStoreFromNodeTask)

            if added:
                invoke_in_main_thread(self._tree_model.append, task)
            else:
                invoke_in_main_thread(self._tree_model.remove, task)

        download_slot.observer.register(download_slot_callback)
