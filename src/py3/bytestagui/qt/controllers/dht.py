'''DHT Network'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from PySide import QtCore # @UnresolvedImport
from bytestagui.base.controllers.dht import (
    DHTClientController as BaseDHTClientController)
from bytestagui.base.views.dht import (CONNECTING_MSG, CONNECTED_MSG, 
    DISCONNECTED_MSG)
from bytestagui.qt.controllers.invoker import invoke_in_main_thread
from bytestagui.qt.controllers.loader import LoaderController


class DHTClientController(BaseDHTClientController):
    def __init__(self, application):
        BaseDHTClientController.__init__(self, application)

        self.observer.register(
            lambda status: invoke_in_main_thread(self._connect_cb, status))

    def _connect_cb(self, status):
        main_window = self.application.singletons[LoaderController].main_window

        if status == BaseDHTClientController.CONNECTING:
            main_window.main_status_bar.showMessage(CONNECTING_MSG)
        elif status == BaseDHTClientController.CONNECTED:
            main_window.main_status_bar.showMessage(CONNECTED_MSG)
        else:
            main_window.main_status_bar.showMessage(DISCONNECTED_MSG)
