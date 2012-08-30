'''DHT networking protocols'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from bytestag.dht.models import (NodeList, JSONKeys, KVPExchangeInfoList,
    KVPExchangeInfo)
from bytestag.dht.tables import Bucket, RoutingTable, Node, BucketFullError
from bytestag.events import (EventReactorMixin, EventScheduler, EventID,
    asynchronous, Task, Observer, FnTaskSlot, WrappedThreadPoolExecutor)
from bytestag.keys import KeyBytes, compute_bucket_number, random_bucket_key
from bytestag.network import Network, DownloadTask
from bytestag.tables import KVPID
import collections
import io
import logging
import math
import socket
import threading
import time


__docformat__ = 'restructuredtext en'
_logger = logging.getLogger(__name__)


class FindValueFromNodeResult(collections.namedtuple('FindValueFromNodeResult',
    ['kvp_info_list', 'node_list'])):
    '''A named tuple representing key-value pair information or additional
    nodes.'''

    __slots__ = ()


class DHTNetwork(EventReactorMixin):
    '''The distributed hash table network

    :CVariables:
        NETWORK_ID
            The unique network id reserved only use in the Bytestag network.
    '''

    NETWORK_ID = 'BYTESTAG'
    MAX_VALUE_SIZE = 1048576  # 1 MB
    NETWORK_PARALLELISM = 3  # constant alpha
    TIME_EXPIRE = 86490  # seconds. time-to-live from original publication date
    TIME_REFRESH = 3600  # seconds. time to refresh unaccessed bucket
    TIME_REPLICATE = 3600  # seconds. interval between replication events
    TIME_REPUBLISH = 86400  # seconds. time after original publisher must
    # republish

    def __init__(self, event_reactor, kvp_table, node_id=None, network=None,
    download_slot=None):
        '''Init

        :Parameters:
            event_reactor : :class:`.EventReactor`
                The Event Reactor
            kvp_table : :class:`.KVPTable`
                The storage
            node_id : :class:`.KeyBytes`
                A key to be used as the node id.
        '''

        EventReactorMixin.__init__(self, event_reactor)
        self._network = network or Network(event_reactor)
        self._network.receive_callback = self._receive_callback
        self._routing_table = RoutingTable()
        self._key = node_id or KeyBytes()
        self._pool_executor = WrappedThreadPoolExecutor(
            Network.DEFAULT_POOL_SIZE / 2, event_reactor)
        self._kvp_table = kvp_table
        self._event_scheduler = EventScheduler(event_reactor)
        self._refresh_timer_id = EventID(self, 'Refresh')
        self._download_slot = download_slot or FnTaskSlot()

        self._setup_timers()

    def _setup_timers(self):
        self._event_scheduler.add_periodic(DHTNetwork.TIME_REFRESH / 4,
            self._refresh_timer_id)
        self._event_reactor.register_handler(self._refresh_timer_id,
            self._refresh_buckets)

    @property
    def routing_table(self):
        '''The routing table

        :rtype: :class:`.RoutingTable`
        '''

        return self._routing_table

    @property
    def key(self):
        '''The node id

        :rtype: :class:`.KeyBytes`
        '''

        return self._key

    @property
    def node(self):
        '''The node info

        :rtype: `Node`
        '''

        return Node(self._key, self.address)

    @property
    def address(self):
        '''The address of the server

        :return: A ``tuple`` holding host and port number.
        :rtype: ``tuple``
        '''

        return self._network.server_address

    @property
    def download_slot(self):
        '''The :class:`.FnTaskSlot` which holds
        :class:`.ReadStoreFromNodeTask`.'''

        return self._download_slot

    def _template_dict(self):
        '''Return a new dict holding common stuff like network id'''

        d = {
            JSONKeys.NETWORK_ID: DHTNetwork.NETWORK_ID,
            JSONKeys.NODE_ID: self._key.base64,
        }

        return d

    def _receive_callback(self, data_packet):
        '''An incoming packet callback'''

        dict_obj = data_packet.dict_obj

        if dict_obj.get(JSONKeys.NETWORK_ID) != DHTNetwork.NETWORK_ID:
            _logger.debug('Unknown network id, discarding. %s←%s',
                self.address, data_packet.address)
            return

        self._update_routing_table_from_data_packet(data_packet)

        rpc_name = dict_obj.get(JSONKeys.RPC)

        rpc_map = {
            JSONKeys.RPCs.PING: self._received_ping_rpc,
            JSONKeys.RPCs.FIND_NODE: self._received_find_node_rpc,
            JSONKeys.RPCs.FIND_VALUE: self._received_find_value_rpc,
            JSONKeys.RPCs.GET_VALUE: self._received_get_value_rpc,
            JSONKeys.RPCs.STORE: self._received_store_rpc,
        }

        fn = rpc_map.get(rpc_name)

        if fn:
            _logger.debug('Got rpc %s', rpc_name)
            fn(data_packet)
        else:
            _logger.debug('Received unknown rpc %s', rpc_name)

    def join_network(self, address):
        '''Join the network

        :rtype: :class:`JoinNetworkTask`
        :return: A future that returns ``bool``. If ``True``, the join was
            successful.
        '''

        _logger.debug('Join %s→%s', self.address, address)

        join_network_task = JoinNetworkTask(self, address)

        self._pool_executor.submit(join_network_task)

        return join_network_task

    def ping_address(self, address):
        '''Ping an address

        :rtype: :class:`PingTask`
        :return: A future which returns ``bool`` or a tuple of
            (``float``, `Node`). If a tuple is returned,
            the ping was successful. The items represents the ping time and
            the node.
        '''

        _logger.debug('Ping %s→%s', self.address, address)

        ping_task = PingTask(address, self)

        self._pool_executor.submit(ping_task)

        return ping_task

    def ping_node(self, node):
        '''Ping a node

        :see: `ping_address`
        :rtype: :class:`PingTask`
        '''

        return self.ping_address(node.address)

    def _received_ping_rpc(self, data_packet):
        '''Ping RPC callback'''

        _logger.debug('Pong %s→%s', self.address, data_packet.address)

        d = self._template_dict()

        self._network.send_answer_reply(data_packet, d)

    def find_nodes_from_node(self, node, key):
        '''Find the closest nodes to a key

        :rtype: :class:`FindNodesFromNodeTask`
        :return: A future which returns a `NodeList` or ``None``.
        '''

        _logger.debug('Find node %s→%s %s', self.node, node, key)

        find_nodes_from_node_task = FindNodesFromNodeTask(self, node, key)

        self._pool_executor.submit(find_nodes_from_node_task)

        return find_nodes_from_node_task

    def find_value_from_node(self, node, key, index=None):
        '''Ask a node about values for a key

        :Parameters:
            node: `Node`
                The node to be contacted
            key: :class:`.KeyBytes`
                The key of the value
            index: :class:`.KeyBytes`, ``None``
                If given, the request will be filtered to that given index.

        :rtype: :class:`FindValueFromNodeTask`
        :return: A future which returns a `FindValueFromNodeResult` or
            ``None``.
        '''

        _logger.debug('Find value %s:%s %s→%s', key, index, self.node,
            node)

        find_value_from_node_task = FindValueFromNodeTask(self,
            node, key, index)

        self._pool_executor.submit(find_value_from_node_task)

        return find_value_from_node_task

    def _received_find_node_rpc(self, data_packet):
        '''Find node RPC callback'''

        _logger.debug('Find node %s←%s', self.address,
            data_packet.address)

        key_obj = KeyBytes.new_silent(data_packet.dict_obj.get(JSONKeys.KEY))

        if not key_obj:
            _logger.debug('Find node %s←%s bad key', self.address,
            data_packet.address)
            return

        self._reply_find_node(data_packet, key_obj)

    def _reply_find_node(self, data_packet, key_obj):
        '''Reply to a find node rpc'''

        nodes = self._routing_table.get_close_nodes(key_obj,
            Bucket.MAX_BUCKET_SIZE)
        node_list = NodeList(nodes).to_json_dumpable()
        d = self._template_dict()
        d[JSONKeys.NODES] = node_list

        _logger.debug('Find node reply %s→%s len=%d',
            self.address, data_packet.address, len(node_list))
        self._network.send_answer_reply(data_packet, d)

    def _received_find_value_rpc(self, data_packet):
        '''Find value rpc callback'''

        _logger.debug('Find value %s←%s', self.address,
            data_packet.address)

        key = KeyBytes.new_silent(data_packet.dict_obj.get(JSONKeys.KEY,
            'fake'))
        index = KeyBytes.new_silent(data_packet.dict_obj.get(JSONKeys.INDEX))

        if not key:
            _logger.debug('Find value %s←%s bad key', self.address,
            data_packet.address)
            return

        _logger.debug('Find value %s←%s k=%s i=%s', self.address,
            data_packet.address, key, index)

        kvpid = KVPID(key, index)

        if index and kvpid in self._kvp_table:
            kvp_record = self._kvp_table.record(kvpid)

            d = self._template_dict()
            d[JSONKeys.VALUES] = KVPExchangeInfoList([
                KVPExchangeInfo.from_kvp_record(kvp_record)
            ]).to_json_dumpable()

            self._network.send_answer_reply(data_packet, d)
        elif self._kvp_table.indices(key):
            kvp_record_list = self._kvp_table.records_by_key(key)

            d = self._template_dict()
            d[JSONKeys.VALUES] = KVPExchangeInfoList.from_kvp_record_list(
                kvp_record_list).to_json_dumpable()

            self._network.send_answer_reply(data_packet, d)
        else:
            self._reply_find_node(data_packet, key)

    def find_node_shortlist(self, key):
        '''Return nodes close to a key

        :rtype: :class:`FindShortlistTask`
        '''

        _logger.debug('Find nodes k=%s', key)

        find_shortlist_task = FindShortlistTask(self, key,
            find_nodes=True)

        self._pool_executor.submit(find_shortlist_task)

        return find_shortlist_task

    def find_value_shortlist(self, key, index=None):
        '''Return nodes close to a key and may have the value

        :rtype: :class:`FindShortlistTask`
        '''

        _logger.debug('Find value k=%s', key)

        find_shortlist_task = FindShortlistTask(self, key, index=index,
            find_nodes=False)

        self._pool_executor.submit(find_shortlist_task)

        return find_shortlist_task

    def _data_packet_to_node(self, data_packet):
        '''Extract node info from a packet

        :rtype: :class:`Node`
        '''

        address = data_packet.address

        try:
            node_key = KeyBytes(data_packet.dict_obj.get(JSONKeys.NODE_ID))
        except Exception as e:
            _logger.debug('Ignore key error %s', e)
            return

        return Node(node_key, address)

    def _update_routing_table_from_data_packet(self, data_packet):
        '''Extract node and update routing table from a data packet'''

        node = self._data_packet_to_node(data_packet)

        if node:
            self._update_routing_table(node)

    def _update_routing_table(self, node):
        '''Update the routing table with this node.

        The node must have contacted us or it has responded.
        '''

        if node.key == self._key:
            _logger.debug('Ignore node %s with our id on routing table update',
                node)
            return

        try:
            self._routing_table.node_update(node)
        except BucketFullError as e:
            bucket = e.bucket
            old_node = e.node

            self._update_full_bucket(bucket, old_node, node)

    @asynchronous(name='update_full_bucket')
    def _update_full_bucket(self, bucket, old_node, new_node):
        '''A full bucket callback that will ping and update the buckets'''

        _logger.debug('Update routing table, bucket=%s full', bucket)

        future = self.ping_node(old_node)
        has_responded = future.result()

        if not has_responded:
            _logger.debug('Bucket %s drop %s add %s', bucket, old_node,
                new_node)
            bucket.keep_new_node()
        else:
            _logger.debug('Bucket %s keep %s ignore %s', bucket, old_node,
                new_node)
            bucket.keep_old_node()

    def get_value_from_node(self, node, key, index=None, offset=None):
        '''Download, from a node, data value associated to the key

        :rtype: :class:`.DownloadTask`
        '''

        transfer_id = self._network.new_sequence_id()
        d = self._template_dict()
        d[JSONKeys.RPC] = JSONKeys.RPCs.GET_VALUE
        d[JSONKeys.KEY] = key.base64
        d[JSONKeys.INDEX] = index.base64 if index else key.base64
        d[JSONKeys.TRANSFER_ID] = transfer_id

        if offset:
            d[JSONKeys.VALUE_OFFSET] = offset

        task = self._network.expect_incoming_transfer(transfer_id)

        _logger.debug('Get value %s→%s transfer_id=%s', self.node, node,
            transfer_id)

        self._network.send(node.address, d)

        return task

    @asynchronous(name='received_get_value_rpc')
    def _received_get_value_rpc(self, data_packet):
        '''Get value rpc calllback'''

        _logger.debug('Get value %s←%s', self.address,
            data_packet.address)

        self._update_routing_table_from_data_packet(data_packet)

        key = KeyBytes.new_silent(data_packet.dict_obj[JSONKeys.KEY])
        index = KeyBytes.new_silent(data_packet.dict_obj[JSONKeys.INDEX])
        transfer_id = data_packet.dict_obj.get(JSONKeys.TRANSFER_ID)

        if not transfer_id:
            _logger.debug('Missing transfer id')
            return

        try:
            offset = data_packet.dict_obj.get(JSONKeys.VALUE_OFFSET, 0)
        except TypeError as e:
            _logger.debug('Offset parse error %s', e)

            return

        kvpid = KVPID(key, index)

        if not kvpid in self._kvp_table:
            _logger.debug('KeyBytes not in cache')
            return

        data = self._kvp_table[kvpid]

        task = self._network.send_bytes(data_packet.address,
            transfer_id, data[offset:])
        bytes_sent = task.result()

        _logger.debug('Sent %d bytes', bytes_sent)

    def store_to_node(self, node, key, index, bytes_, timestamp):
        '''Send data to node.

        :rtype: :class:`StoreToNodeTask`
        '''

        _logger.debug('Store value %s→%s', self.node, node)

        store_to_node_task = StoreToNodeTask(self, node, key, index,
            bytes_, timestamp)

        self._pool_executor.submit(store_to_node_task)

        return store_to_node_task

    @asynchronous(name='received_store_rpc')
    def _received_store_rpc(self, data_packet):
        '''Received store RPC'''

        _logger.debug('Store value %s←%s', self.address, data_packet.address)

        dict_obj = data_packet.dict_obj

        # FIXME: validation
        key = KeyBytes(dict_obj[JSONKeys.KEY])
        index = KeyBytes(dict_obj[JSONKeys.INDEX])
        size = int(dict_obj[JSONKeys.SIZE])
        timestamp = int(dict_obj[JSONKeys.TIMESTAMP])

        d = self._template_dict()
        kvpid = KVPID(key, index)

        if self._kvp_table.is_acceptable(kvpid, size, timestamp):
            transfer_id = self._network.new_sequence_id()

            download_task = self._download_slot.add(
                self._network.expect_incoming_transfer, transfer_id,
                max_size=DHTNetwork.MAX_VALUE_SIZE,
                download_task_class=ReadStoreFromNodeTask)

            download_task.key = kvpid.key
            download_task.index = kvpid.index
            download_task.total_size = size
            d[JSONKeys.TRANSFER_ID] = transfer_id

            self._network.send_answer_reply(data_packet, d)

            _logger.debug('Store value %s←%s begin read', self.address,
                data_packet.address)

            file = download_task.result()

            _logger.debug('Store value %s←%s received data', self.address,
                data_packet.address)

            data = file.read()

            if index.validate_value(data):
                self._kvp_table[kvpid] = data
                kvp_record = self._kvp_table.record(kvpid)
                kvp_record.timestamp = timestamp
                kvp_record.last_update = time.time()
                kvp_record.time_to_live = self._calculate_expiration_time(key)
        else:
            self._network.send_answer_reply(data_packet, d)

    def _calculate_expiration_time(self, key):
        '''Return the expiration time for a given key'''

        bucket_number = compute_bucket_number(self.key, key)
        num_contacts = sum(
            [len(self.routing_table[i]) for i in range(bucket_number)])
        num_bucket_contacts = self._routing_table.count_close(key)

        c = num_contacts + num_bucket_contacts

        if c < Bucket.MAX_BUCKET_SIZE == 0:
            return DHTNetwork.TIME_EXPIRE
        else:
            return DHTNetwork.TIME_EXPIRE / math.exp(
                c / Bucket.MAX_BUCKET_SIZE)

    @asynchronous(name='refresh buckets')
    def _refresh_buckets(self, event_id):
        for bucket in self._routing_table.buckets:
            if bucket.last_update + DHTNetwork.TIME_REFRESH < time.time():
                key = random_bucket_key(self.node.key, bucket.number)
                task = self.find_node_shortlist(key)
                task.result()

    def store_value(self, key, index):
        '''Publish or replicate value to nodes.

        :rtype: :class:`StoreValueTask`
        '''

        _logger.debug('Store value %s:%s', key, index)

        store_value_task = StoreValueTask(self, key, index)

        self._pool_executor.submit(store_value_task)

        return store_value_task

    def get_value(self, key, index):
        get_value_task = GetValueTask(self, key, index)

        self._download_slot.queue(get_value_task)

        return get_value_task


class Shortlist(object):
    '''A shortlist containing close nodes to a key'''

    def __init__(self, key_obj, routing_table, server_node):
        self._key_obj = key_obj
        self._routing_table = routing_table
        self._active_nodes = set()
        self._contacted_nodes = set()
        self._uncontacted_nodes = set()
        self._useful_nodes = set()
        self._nodes = set()
        self._closest_node = None
        self._lock = threading.Lock()
        self._server_node = server_node
        self._intial_closest_node = None
        self._closest_node = None
        self._iteration_count = 0
#        self._data_size_counter = collections.Counter()
        self._key_to_nodes_map = collections.defaultdict(set)
        self._key_to_size_counter_map = collections.defaultdict(
            collections.Counter)
        self._key_to_timestamp_counter_map = collections.defaultdict(
            collections.Counter)

        self._initial_nodes()

    @property
    def nodes(self):
        '''The nodes in the shortlist.

        :rtype: ``set``
        '''

        return self._nodes

    @property
    def useful_nodes(self):
        '''The nodes that may have the value associated to the key.

        :rtype: ``set``
        '''

        return self._useful_nodes

    @property
    def sorted_nodes(self):
        '''The nodes sorted by distance.

        The first node is the closest.

        :rtype: ``list``
        '''

        node_list = NodeList(self._nodes)
        node_list.sort_distance(self._key_obj)

        return node_list

    def _initial_nodes(self, count=DHTNetwork.NETWORK_PARALLELISM):
        '''Set up the first ``alpha`` nodes'''

        nodes = set(self._routing_table.get_close_nodes(self._key_obj))

        self._nodes.update(nodes)
        self._uncontacted_nodes.update(nodes)

        if self._nodes:
            self._closest_node = self.sorted_nodes[0]
            self._intial_closest_node = self._closest_node

    def _update_closest(self):
        '''Set the closet node'''

        if self._nodes:
            self._closest_node = self.sorted_nodes[0]

    def get_nodes_for_contacting(self,
    count=DHTNetwork.NETWORK_PARALLELISM):
        '''Pop nodes off uncontacted list

        :rtype: ``list``
        '''

        nodes = []

        with self._lock:
            for dummy in range(count):
                try:
                    node = self._uncontacted_nodes.pop()
                except KeyError:
                    break

                self._contacted_nodes.add(node)
                nodes.append(node)

            self._iteration_count += 1

        return nodes

    def mark_node(self, node, active, useful=False,
    kvp_exchange_info_list=None):
        '''Add or remove the node from the shortlist.

        :Parameters:
            node: `Node`
                The node
            active: `bool`
                Whether the node responded
            useful: `bool`
                If `True`, the node has the value
            data_size: `int`
                The size of the value

        Call this using the nodes from `get_nodes_for_contacting`.
        '''

        assert node in self._nodes

        with self._lock:
            if not active:
                self._nodes.remove(node)
                self._active_nodes.add(node)

            if useful:
                self._useful_nodes.add(node)

            if kvp_exchange_info_list:
                for kvp_exchange_info in kvp_exchange_info_list:
                    key = kvp_exchange_info.key
                    index = kvp_exchange_info.index
                    size = kvp_exchange_info.size
                    timestamp = kvp_exchange_info.timestamp
                    self._key_to_nodes_map[(key, index)].add(node)
                    self._key_to_size_counter_map[(key, index)].update([size])
                    self._key_to_timestamp_counter_map[(key, index)
                        ].update([timestamp])

    def add_nodes(self, node_list):
        '''Add more possible nodes to contact'''

        nodes = set(node_list)

        nodes.discard(self._server_node)
        nodes.difference_update(self._contacted_nodes)

        with self._lock:
            self._nodes.update(nodes)
            self._uncontacted_nodes.update(nodes)
            self._update_closest()

    def is_finished(self):
        '''Return whether the shortlist is complete

        :rtype: ``bool``
        '''

        limit_condition = len(self._active_nodes) >= Bucket.MAX_BUCKET_SIZE \
            or len(self._uncontacted_nodes) == 0
        improvement_condition = self._iteration_count >= 2 \
            and self._closest_node.key.distance_int(self._key_obj) \
            < self._intial_closest_node.key.distance_int(self._key_obj)

        return limit_condition or improvement_condition

    def get_common_kvp_exchange_info(self, key, index):
        size = self._key_to_size_counter_map[(key, index)].most_common(1)[0]
        timestamp = self._key_to_timestamp_counter_map[(key, index)
            ].most_common(1)[0]

        return KVPExchangeInfo(key, index, size, timestamp)


class PingTask(Task):
    def run(self, address, controller):
        start_time = time.time()
        d = controller._template_dict()
        d[JSONKeys.RPC] = JSONKeys.RPCs.PING

        task = controller._network.send(address, d, timeout=True)

        self.hook_task(task)

        data_packet = task.result()

        if data_packet:
            _logger.debug('Pong %s←%s', controller.address, address)
            controller._update_routing_table_from_data_packet(data_packet)
            node = controller._data_packet_to_node(data_packet)

            return (time.time() - start_time, node)
        else:
            _logger.debug('Pong timeout %s←%s', controller.address,
                address)

            return False


class FindNodesFromNodeTask(Task):
    def run(self, controller, node, key):
        d = controller._template_dict()
        d[JSONKeys.RPC] = JSONKeys.RPCs.FIND_NODE
        d[JSONKeys.KEY] = key.base64

        task = controller._network.send(node.address, d, timeout=True)

        self.hook_task(task)

        data_packet = task.result()

        if not data_packet:
            _logger.debug('Find node timeout %s←%s', controller.node, node)
            return

        controller._update_routing_table_from_data_packet(data_packet)

        dict_obj = data_packet.dict_obj
        node_list = dict_obj.get(JSONKeys.NODES)

        if node_list:
            try:
                nodes = NodeList.from_json_loadable(node_list)
            except ValueError as e:
                _logger.debug('Find node invalid %s←%s err=%s',
                    controller.node, node, e)
            else:
                _logger.debug('Find node nodes %s←%s len=%d',
                    controller.node, node, len(nodes))
                return nodes

        _logger.debug('Find node invalid %s←%s', controller.node, node)


class FindValueFromNodeTask(Task):
    def run(self, controller, node, key, index):
        d = controller._template_dict()
        d[JSONKeys.RPC] = JSONKeys.RPCs.FIND_VALUE
        d[JSONKeys.KEY] = key.base64

        if index:
            d[JSONKeys.INDEX] = index.base64

        future = controller._network.send(node.address, d, timeout=True)
        data_packet = future.result()

        if not data_packet:
            _logger.debug('Find value timeout %s←%s', controller.node, node)
            return

        controller._update_routing_table_from_data_packet(data_packet)

        dict_obj = data_packet.dict_obj

        if JSONKeys.VALUES in dict_obj:
            kvp_info_list = KVPExchangeInfoList.from_json_loadable(
                dict_obj[JSONKeys.VALUES])

            _logger.debug('Find value %s←%s dictlen=%d',
                controller.node, node, len(kvp_info_list))

            return FindValueFromNodeResult(kvp_info_list, None)

        elif JSONKeys.NODES in dict_obj:
            try:
                nodes = NodeList.from_json_loadable(dict_obj[JSONKeys.NODES])
            except ValueError as e:
                _logger.debug('Find value node invalid %s←%s err=%s',
                    controller.node, node, e)
            else:
                _logger.debug('Find value nodes %s←%s len=%d',
                    controller.node, node, len(nodes))
                return FindValueFromNodeResult(None, nodes)


class StoreToNodeTask(Task):
    '''Returns the number of bytes sent'''

    def __init__(self, *args, **kwargs):
        Task.__init__(self, *args, **kwargs)
        self.node = args[1]
        self.key = args[2]
        self.index = args[3]
        self.total_size = len(args[4])

    def run(self, controller, node, key, index, bytes_, timestamp):
        d = controller._template_dict()
        d[JSONKeys.RPC] = JSONKeys.RPCs.STORE
        d[JSONKeys.KEY] = key.base64
        d[JSONKeys.INDEX] = index.base64
        d[JSONKeys.SIZE] = len(bytes_)
        d[JSONKeys.TIMESTAMP] = timestamp or time.time()

        _logger.debug('Uploading to %s', node)

        send_task = controller._network.send(node.address, d, timeout=True)

        self.hook_task(send_task)

        data_packet = send_task.result()

        if not data_packet:
            return 0

        if JSONKeys.TRANSFER_ID in data_packet.dict_obj:
            transfer_id = data_packet.dict_obj[JSONKeys.TRANSFER_ID]
            send_file_task = controller._network.send_bytes(node.address,
                transfer_id, bytes_)

            self.hook_task(send_file_task)

            return send_file_task.result()
        else:
            return 0


class FindShortlistTask(Task):
    '''Returns `Shortlist`'''

    def run(self, controller, key, index=None, find_nodes=True):
        '''find x loop'''

        shortlist = Shortlist(key, controller._routing_table, controller.node)

        while True:
            _logger.debug('Find node/value iteration')

            if shortlist.is_finished():
                _logger.debug('Find node/value iteration finished')
                break

            if find_nodes:
                self._find_node_iteration(controller, shortlist, key)
            else:
                self._find_value_iteration(controller, shortlist, key, index)

        _logger.debug('Find node/value done len=%d', len(shortlist.nodes))

        return shortlist

    def _find_node_iteration(self, controller, shortlist, key_obj):
        '''An iteration to find nodes to add to shortlist'''

        nodes = shortlist.get_nodes_for_contacting()
        things = []

        for node in nodes:
            task = controller.find_nodes_from_node(node, key_obj)

            self.hook_task(task)
            things.append((node, task))

        for node, task in things:
            nodes = task.result()

            if nodes is not None:
                _logger.debug('Find node iteration %s←%s len=%d',
                    controller.node, node, len(nodes))
                shortlist.add_nodes(nodes)
                shortlist.mark_node(node, True)
            else:
                _logger.debug('Find node iteration timeout %s←%s ',
                    controller.node, node)
                shortlist.mark_node(node, False)

    def _find_value_iteration(self, controller, shortlist, key, index):
        '''An iteration to find useful nodes to add to shortlist'''

        nodes = shortlist.get_nodes_for_contacting()
        things = []

        for node in nodes:
            task = controller.find_value_from_node(node, key, index)

            self.hook_task(task)
            things.append((node, task))

        for node, task in things:
            find_value_result = task.result()

            if not find_value_result:
                _logger.debug('Find value iteration timeout %s←%s ',
                    controller.node, node)
                shortlist.mark_node(node, False)
            elif find_value_result.node_list:
                nodes = find_value_result.node_list

                _logger.debug('Find value iteration %s←%s nodes len=%d',
                    controller.node, node, len(nodes))
                shortlist.add_nodes(nodes)
                shortlist.mark_node(node, True)
            elif find_value_result.kvp_info_list:
                kvp_info_list = find_value_result.kvp_info_list

                _logger.debug('Find value iteration %s←%s value',
                    controller.node, node)

                shortlist.mark_node(node, True, True, kvp_info_list)


class JoinNetworkTask(Task):
    def run(self, controller, address):
        _logger.info('Joining network')

        address = (socket.gethostbyname(address[0]),) + address[1:]
        task = controller.ping_address(address)

        self.hook_task(task)

        result = task.result()

        _logger.debug('Join network ping result %s', result)

        if not result:
            return False

        node = result[1]
        task = controller.find_nodes_from_node(node, controller.key)

        self.hook_task(task)

        node_list = task.result()

        _logger.debug('Join network find nodes result %s', node_list)

        if node_list:
            for node in node_list:
                controller._update_routing_table(node)

            return True
        else:
            return False


class StoreValueTask(Task):
    '''Stores a value to many nodes'''

    def __init__(self, *args, **kwargs):
        Task.__init__(self, *args, **kwargs)
        self._store_to_node_task_observer = Observer()

    @property
    def store_to_node_task_observer(self):
        '''Observer for when :class:`StoreToNodeTask` is started and finished.

        The first argument of the callback is :obj:`bool`. If `True`, the
        task was created. Otherwise, the task was finished. The second
        argument is :class:`StoreToNodeTask`
        '''

        return self._store_to_node_task_observer

    def run(self, controller, key, index):
        kvpid = KVPID(key, index)
        kvp_record = controller._kvp_table.record(kvpid)

        task = controller.find_value_shortlist(key, index)

        self.hook_task(task)

        shortlist = task.result()

        node_list = NodeList(list(shortlist.nodes - shortlist.useful_nodes))
        node_list.sort_distance(controller.key)

        nodes = collections.deque(node_list)
        kvp_record.last_update = time.time()

        _logger.debug('Uploading value %s', kvpid)

        store_count = 0

        if not nodes and not shortlist.useful_nodes:
            _logger.warning('No destination nodes for publication')
            _logger.debug('%s', controller._routing_table)

        while len(nodes):
            tasks = []
            for dummy in range(DHTNetwork.NETWORK_PARALLELISM):
                try:
                    node = nodes.popleft()
                except IndexError:
                    break

                value = controller._kvp_table[kvpid]

                task = controller.store_to_node(node, key, index, value,
                    kvp_record.timestamp)

                self.hook_task(task)
                self._store_to_node_task_observer(True, task)

                tasks.append(task)

            for task in tasks:
                bytes_sent = task.result()
                self._store_to_node_task_observer(False, task)

                if bytes_sent:
                    store_count += 1

        return store_count


class GetValueTask(Task):
    '''Returns the ``bytes``'''

    def run(self, controller, key, index):
        _logger.info('Downloading %s:%s', key.base16, index.base16)
        self._controller = controller
        self._key = key
        self._index = index
        find_value_task = controller.find_value(key, index)

        self.hook_task(find_value_task)

        self._shortlist = find_value_task.result()
        self._useful_node_list = NodeList(self._shortlist.useful_nodes)

        if not self.useful_node_list:
            return None

        self._useful_node_list.sort_distance(key)
        self._kvp_exchange_info = self._shortlist.get_common_kvp_exchange_info(
            key, index)

        for dummy in range(3):
            self._file = io.BytesIO()

            if self._download_round():
                break
            else:
                self._file = None

        if self.file:
            self._replicate_value()

            return self._file.value()

    def _download_round(self):
        _logger.debug('Download round')

        for node in self._useful_node_list:
            download_task = self._controller.get_value_from_node(node,
                self._key, self._index, offset=self._file.tell())

            self.hook_task(download_task)

            transfered_file = download_task.result()
            data = transfered_file.read()

            self._file.write(data)

            if self._file.tell() >= self._data_size:
                break

        return self._index.validate_value(data)

    def _replicate_value(self):
        node_list = self._shortlist.sorted_nodes

        if node_list:
            node = node_list[0]

            if node not in self._shortlist.useful_nodes:
                _logger.debug('Replicating value')

                self._controller.store_to_node(node, self._key, self._index,
                    self._file.value(), self._kvp_exchange_info.timestamp)


class ReadStoreFromNodeTask(DownloadTask):
    def __init__(self, *args, **kwargs):
        DownloadTask.__init__(self, *args, **kwargs)
        self.key = None
        self.index = None
        self.total_size = None
