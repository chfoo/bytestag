'''Client interfaces'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
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
    known_node_address=None):
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

    @property
    def cache_table(self):
        return self._cache_table

    @property
    def shared_files_table(self):
        return self._shared_files_table

    def run(self):
        self._upload_slot = FnTaskSlot()
        self._dht_network = DHTNetwork(self._event_reactor,
            self._aggregated_kvp_table, self._node_id, self._network)
        self._publisher = Publisher(self._event_reactor, self._dht_network,
            self._aggregated_kvp_table, self._upload_slot)
        self._replicator = Replicator(self._event_reactor, self._dht_network,
            self._aggregated_kvp_table, self._upload_slot)

        if self._known_node_address:
            self._dht_network.join_network(self._known_node_address)
            # TODO: put warning if join fails, but don't check on
            # the same thread as the event_reactor

        self._shared_files_table.hash_directories()
        self._event_reactor.start()

    def stop(self):
        self._event_reactor.put(EventReactor.STOP_ID)
