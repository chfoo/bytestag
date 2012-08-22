from bytestag import basedir
from bytestag.client import Client
from bytestag.events import Observer
from bytestag.keys import KeyBytes
from bytestag.ui.controllers.base import BaseController
from bytestag.ui.controllers.builder import BuilderController
from bytestag.ui.controllers.config import ConfigController
from gi.repository import GLib # @UnresolvedImport
import os


class DHTClientController(BaseController):
    def __init__(self, application):
        BaseController.__init__(self, application)

        config_parser = self.application.singletons[
            ConfigController].config_parser

        host = config_parser['network']['host']
        port = int(config_parser['network']['port'])
        node_id = KeyBytes(config_parser['network']['node_id'])

        known_node_host = config_parser['known_nodes']['host1']
        known_node_port = int(config_parser['known_nodes']['port1'])
        self._known_node_address = (known_node_host, known_node_port)

        os.makedirs(basedir.cache_dir, mode=0o777, exist_ok=True)

        self._client = Client(basedir.cache_dir, (host, port), node_id)
        self._client.start()

        builder = self.application.singletons[BuilderController].builder
        statusbar = builder.get_object('main_statusbar')
        self._statusbar = statusbar
        self._context_id = statusbar.get_context_id('DHT Network')

        GLib.timeout_add(100, self._join_network)

    @property
    def client(self):
        return self._client

    def _join_network(self):
        self._statusbar.pop(self._context_id)
        self._statusbar.push(self._context_id, 'Connecting to network…')

        join_network_task = self._client.dht_network.join_network(
            self._known_node_address)

        def cb(result):
            self._statusbar.pop(self._context_id)

            if result:
                self._statusbar.push(self._context_id, 'Connected to network.')
            else:
                self._statusbar.push(self._context_id,
                    'Could not connect to network.')

        join_network_task.observer.register(
            lambda *args: GLib.idle_add(cb(*args)))
