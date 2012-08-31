'''DHT Network'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from bytestagui.base.controllers.dht import BaseDHTClientController
from bytestagui.base.views.dht import (CONNECTING_MSG, CONNECTED_MSG,
    DISCONNECTED_MSG)
from bytestagui.gtk.controllers.inflater import InflaterController
from gi.repository import GLib # @UnresolvedImport


class DHTClientController(BaseDHTClientController):
    def __init__(self, application):
        BaseDHTClientController.__init__(self, application)
        builder = self.application.singletons[InflaterController].main_builder
        self._statusbar = builder.get_object('main_statusbar')
        self._context_id = self._statusbar.get_context_id('DHT Network')

        self.observer.register(
            lambda *args: GLib.idle_add(self._connect_cb, *args))

    def _connect_cb(self, status):
        self._statusbar.pop(self._context_id)

        if status == BaseDHTClientController.CONNECTING:
            self._statusbar.push(self._context_id, CONNECTING_MSG)
        elif status == BaseDHTClientController.CONNECTED:
            self._statusbar.push(self._context_id, CONNECTED_MSG)
        else:
            self._statusbar.push(self._context_id, DISCONNECTED_MSG)
