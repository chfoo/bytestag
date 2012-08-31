'''Client interfaces'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from bytestag import basedir
from bytestag.dht.downloading import Downloader
from bytestag.dht.network import DHTNetwork
from bytestag.dht.publishing import Publisher, Replicator
from bytestag.events import EventReactor, FnTaskSlot
from bytestag.keys import KeyBytes
from bytestag.network import Network
from bytestag.storage import DatabaseKVPTable, SharedFilesKVPTable
from bytestag.tables import AggregatedKVPTable
import logging
import os.path
import threading

__docformat__ = 'restructuredtext en'
_logger = logging.getLogger(__name__)


class Client(threading.Thread):
    '''Client interface.

    :warning: this class is under development.
    '''

    def __init__(self, cache_dir, address=('0.0.0.0', 0), node_id=None,
    known_node_address=None, initial_scan=False, config_dir=None):
        threading.Thread.__init__(self)
        self.daemon = True
        self.name = '{}.{}'.format(__name__, Client.__name__)
        self._event_reactor = EventReactor()
        self._node_id = node_id or KeyBytes()
        self._network = Network(self._event_reactor, address=address)
        self._cache_table = DatabaseKVPTable(
            os.path.join(cache_dir, 'cache.db'))
        self._shared_files_table = SharedFilesKVPTable(
            os.path.join(cache_dir, 'shared_files.db'))
        self._aggregated_kvp_table = AggregatedKVPTable(self._cache_table,
            [self._cache_table, self._shared_files_table])
        self._known_node_address = known_node_address
        self._upload_slot = FnTaskSlot()
        self._download_slot = FnTaskSlot()
        self._initial_scan = initial_scan
        self._config_dir = config_dir or basedir.config_dir

        self._init()

    @property
    def cache_table(self):
        '''The :class:`DatabaseKVPTable`'''
        return self._cache_table

    @property
    def shared_files_table(self):
        '''The :class:`SharedFilesKVPTable`'''

        return self._shared_files_table

    @property
    def upload_slot(self):
        '''The :class:`.FnTaskSlot` which holds :class:`.StoreValueTask`.'''

        return self._upload_slot

    @property
    def download_slot(self):
        '''Download slot.

        :see: :func:`.DHTNetwork.download_slot`
        '''

        return self._download_slot

    @property
    def dht_network(self):
        return self._dht_network

    @property
    def network(self):
        return self._network

    def _init(self):
        self._dht_network = DHTNetwork(self._event_reactor,
            self._aggregated_kvp_table, self._node_id, self._network,
            self._download_slot)
        self._publisher = Publisher(self._event_reactor, self._dht_network,
            self._aggregated_kvp_table, self._upload_slot)
        self._replicator = Replicator(self._event_reactor, self._dht_network,
            self._aggregated_kvp_table, self._upload_slot)
        self._downloader = Downloader(self._event_reactor, self._config_dir,
            self._dht_network, self._download_slot)

    def run(self):
        if self._known_node_address:
            self._dht_network.join_network(self._known_node_address)
            # TODO: put warning if join fails, but don't check on
            # the same thread as the event_reactor

        if self._initial_scan:
            self._shared_files_table.hash_directories()

        self._event_reactor.start()

    def stop(self):
        self._event_reactor.put(EventReactor.STOP_ID)
