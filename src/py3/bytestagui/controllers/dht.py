'''DHT Network'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from bytestag import basedir
from bytestag.client import Client
from bytestag.events import Observer
from bytestag.keys import KeyBytes
from bytestagui.controllers.base import BaseController
from bytestagui.controllers.qt.invoker import invoke_in_main_thread
import abc # @UnusedImport
import os
import threading


class DHTClientController(BaseController, metaclass=abc.ABCMeta):
    '''Provides access to :class:`bytestag.client.Client`'''

    DISCONNECTED, CONNECTING, CONNECTED = range(3)

    def __init__(self, application):
        BaseController.__init__(self, application)
        self._observer = Observer()

        config = self.application.singletons['ConfigController']

        host = config.get('network', 'host')
        port = int(config.get('network', 'port'))
        node_id = KeyBytes(config.get('network', 'node_id'))

        known_node_host = config.get('known_nodes', 'host1')
        known_node_port = int(config.get('known_nodes', 'port1'))
        self._known_node_address = (known_node_host, known_node_port)

        os.makedirs(basedir.cache_dir, mode=0o777, exist_ok=True)

        self._client = Client(basedir.cache_dir, (host, port), node_id)
        self._client.start()

        thread = threading.Timer(1, self.connect)
        thread.daemon = True
        thread.start()

    @property
    def client(self):
        return self._client

    @property
    def observer(self):
        return self._observer

    def connect(self):
        self.observer(DHTClientController.CONNECTING)

        join_network_task = self._client.dht_network.join_network(
            self._known_node_address)

        def cb(result):
            if result:
                invoke_in_main_thread(self.observer,
                    DHTClientController.CONNECTED)
            else:
                invoke_in_main_thread(self.observer,
                    DHTClientController.DISCONNECTED)

        join_network_task.observer.register(cb)

    def stop(self, wait=True):
        self._client.stop()
        self._client.network._pool_executor.shutdown(wait)
        self._client.dht_network._pool_executor.shutdown(wait)
        self._client.join()
