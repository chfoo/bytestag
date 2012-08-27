'''Transfer screen'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from bytestagui.abstract.controllers.base import BaseController
from bytestagui.abstract.views.transfers import (ADDRESS_TEXT, KEY_TEXT,
    PROGRESS_TEXT)
from bytestagui.qt.controllers.dht import DHTClientController
from bytestagui.qt.controllers.loader import LoaderController
from bytestagui.qt.models.transfers import TransfersTableModel
from PySide import QtCore  # @UnresolvedImport


class TransfersTabController(BaseController):
    def __init__(self, application):
        BaseController.__init__(self, application)

        loader = self.application.singletons[LoaderController]
        self._main_window = loader.main_window

        self._create_table()

    def _create_table(self):
        upload_slot = self.application.singletons[
            DHTClientController].client.upload_slot
        download_slot = self.application.singletons[
            DHTClientController].client.download_slot

        table_view = self._main_window.transfers_table_view
        tree_model = TransfersTableModel(
            ['', ADDRESS_TEXT, KEY_TEXT, PROGRESS_TEXT],
            upload_slot, download_slot)

        table_view.setModel(tree_model)
        self._tree_model = tree_model

        timer = QtCore.QTimer(self.application.app)
        timer.timeout.connect(self._update_table)
        timer.start(200)

    def _update_table(self):
        self._tree_model.emit_data_changed()
