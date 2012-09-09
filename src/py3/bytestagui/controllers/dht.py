'''DHT Network'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from bytestag import basedir
from bytestag.client import Client
from bytestag.events import Observer
from bytestag.keys import KeyBytes
from bytestagui.controllers.base import BaseController
from bytestagui.controllers.config import ConfigController
from bytestagui.controllers.qt.invoker import invoke_in_main_thread
import abc # @UnusedImport
import atexit
import itertools
import os
import random
import threading
import time


class DHTClientController(BaseController, metaclass=abc.ABCMeta):
    '''Provides access to :class:`bytestag.client.Client`'''

    DISCONNECTED, CONNECTING, CONNECTED = range(3)
    CONNECTING_MSG = 'Connecting to network…'
    CONNECTED_MSG = 'Connected to network.'
    DISCONNECTED_MSG = 'Disconnected from network.'

    def __init__(self, application):
        BaseController.__init__(self, application)
        self._observer = Observer()

        config = self.application.singletons[ConfigController]

        host = config.get('network', 'host')
        port = int(config.get('network', 'port'))
        node_id = KeyBytes(config.get('network', 'node_id'))

        use_port_forwarding = config.get('network',
            'enable_port_forwarding', as_bool=True)

        os.makedirs(basedir.cache_dir, mode=0o777, exist_ok=True)

        self._client = Client(basedir.cache_dir, (host, port), node_id,
            use_port_forwarding=use_port_forwarding)
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
        t = 2
        nodes = self._get_known_nodes_from_config()

        random.shuffle(nodes)

        nodes = itertools.cycle(nodes)

        for address in nodes:
            self.observer(DHTClientController.CONNECTING)

            join_network_task = self._client.dht_network.join_network(address)

            result = join_network_task.result()

            if result:
                invoke_in_main_thread(self.observer,
                    DHTClientController.CONNECTED)
                break
            else:
                invoke_in_main_thread(self.observer,
                    DHTClientController.DISCONNECTED)

            t *= 2
            t = min(3600, t)

            time.sleep(t)

    def stop(self, wait=True):
        self._client.stop()
        self._client.network._pool_executor.shutdown(wait)
        self._client.dht_network._pool_executor.shutdown(wait)
        self._client.join()

    def _get_long_lived_nodes(self):
        l = []

        for bucket in self._client.dht_network.routing_table.buckets:
            if bucket.nodes:
                l.append(bucket.nodes[-1].address)

        return l

    def _get_known_nodes_from_config(self):
        config = self.application.singletons[ConfigController]
        config_parser = config.config_parser

        l = []

        l.append((config.get('network', 'default_known_node_host'),
            int(config.get('network', 'default_known_node_port'))))

        for key in config_parser['known_nodes'].keys():
            if key.startswith('node'):
                port_key = 'port{}'.format(key[4:])
                l.append((config.get('shared_files', key),
                    int(config.get('shared_files', port_key))))

        return l

    def _save_known_nodes_to_config(self, nodes):
        config = self.application.singletons[ConfigController]
        config_parser = config.config_parser

        config_parser['known_nodes'] = {}

        for i in range(len(nodes)):
            host, port = nodes[i]

            config.set('known_nodes', 'host{}'.format(i + 1), host)
            config.set('known_nodes', 'port{}'.format(i + 1), port)

        config.save()

    def _save_long_lived_nodes(self):
        self._save_known_nodes_to_config(self._get_long_lived_nodes())
