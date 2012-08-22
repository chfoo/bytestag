from bytestag import basedir
from bytestag.client import Client
from bytestag.keys import KeyBytes
from bytestag.ui.controllers.base import BaseController
from bytestag.ui.controllers.config import ConfigController
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

        os.makedirs(basedir.cache_dir, mode=0o777, exist_ok=True)

        self._client = Client(basedir.cache_dir, (host, port), node_id,
            (known_node_host, known_node_port))

        self._client.start()

    @property
    def client(self):
        return self._client
