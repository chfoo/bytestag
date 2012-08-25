'''DHT Network'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from bytestagui.abstract.controllers.dht import (
    DHTClientController as BaseDHTClientController)
from bytestagui.gtk.controllers.builder import BuilderController
from gi.repository import GLib # @UnresolvedImport


class DHTClientController(BaseDHTClientController):
    def __init__(self, application):
        BaseDHTClientController.__init__(self, application)
        builder = self.application.singletons[BuilderController].builder
        self._statusbar = builder.get_object('main_statusbar')
        self._context_id = self._statusbar.get_context_id('DHT Network')

        self.observer.register(
            lambda *args: GLib.idle_add(self._connect_cb, *args))

    def _connect_cb(self, status):
        self._statusbar.pop(self._context_id)

        if status == BaseDHTClientController.CONNECTING:
            self._statusbar.push(self._context_id, 'Connecting to network…')
        elif status == BaseDHTClientController.CONNECTED:
            self._statusbar.push(self._context_id, 'Connected to network.')
        else:
            self._statusbar.push(self._context_id,
                'Disconnected from network.')
