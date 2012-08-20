from bytestag.dht.network import DHTNetwork, FindValueFromNodeResult
from bytestag.events import EventReactor, EventScheduler
from bytestag.keys import KeyBytes
from bytestag.storage import MemoryKVPTable
from bytestag.tables import KVPID
import hashlib
import logging
import threading
import time
import unittest

_logger = logging.getLogger(__name__)


class TestNetworkControllerMultiNode(unittest.TestCase):
    TIMEOUT = 5

    def setup_nodes(self, count=2):
        _logger.debug('DHTNetwork setup---')

        self.er = []
        self.er_thread = []
        self.nc = []
        self.timer = []

        for i in range(count):
            self.er.append(EventReactor())

            er_thread = threading.Thread(target=self.er[i].start)

            er_thread.daemon = True
            er_thread.name = 'event-reactor-thread-%d' % i
            er_thread.start()
            self.er_thread.append(er_thread)
            self.nc.append(DHTNetwork(self.er[i], MemoryKVPTable()))

            timer = EventScheduler(self.er[i])

            timer.add_one_shot(self.TIMEOUT, EventReactor.STOP_ID)
            self.timer.append(timer)
            _logger.debug('Server %d at %s', i, self.nc[i].address)

        self.stuff = {}

    def stop_event_reactors(self):
        for er in self.er:
            er.put(EventReactor.STOP_ID)

    def join_event_reactors(self):
        for er_thread in self.er_thread:
            er_thread.join()

    def test_ping_address(self):
        '''It should send a ping and receive a response'''

        self.setup_nodes(2)

        future = self.nc[0].ping_address(self.nc[1].address)
        ping_result = future.result()

        self.stuff['ping'] = ping_result

        self.stop_event_reactors()
        self.join_event_reactors()

        self.assertTrue(self.stuff['ping'])

    def test_ping_rpc(self):
        '''It should send a PING and reply with a PONG and both
        contacts are added to routing table'''

        self.setup_nodes(2)

        contact_0 = self.nc[0].node
        contact_1 = self.nc[1].node

        future = self.nc[0].ping_node(contact_1)
        ping_result = future.result()
        self.stuff['server_0'] = ping_result

        self.stop_event_reactors()
        self.join_event_reactors()

        self.assertTrue(self.stuff['server_0'])
        self.assertTrue(contact_0 in self.nc[1].routing_table)
        self.assertTrue(contact_1 in self.nc[0].routing_table)

    def test_find_node_rpc(self):
        '''It should get a list of nodes'''

        num_nodes = 10
        self.setup_nodes(num_nodes)

        # Add the address of the other nodes
        for i in range(1, num_nodes):
            future = self.nc[0].join_network(self.nc[i].address)
            self.assertTrue(future.result())

        logging.debug('SEND FIND NODE')

        future = self.nc[1].find_nodes_from_node(self.nc[0].node, KeyBytes())

        contacts = future.result()

        logging.debug('GOT CONTACTS')

        self.stuff['contacts'] = contacts

        logging.debug('SHUTDOWN')

        self.stop_event_reactors()
        self.join_event_reactors()

        print(self.nc[0].node)
        print(self.nc[0].routing_table)
        print(self.nc[1].node)
        print(self.nc[1].routing_table)
        print(list(map(str, self.stuff['contacts'])))

        self.assertTrue(self.stuff['contacts'])
        self.assertGreaterEqual(len(self.stuff['contacts']), num_nodes / 2)

    def test_find_binary_value_size_from_node(self):
        '''It should get the size of the data from the node'''

        self.setup_nodes(2)

        data = b'\x00\x01\x03' * 500
        key = KeyBytes(hashlib.sha1(data).digest())
        kvp_table = MemoryKVPTable()
        self.nc[1]._kvp_table = kvp_table
        kvpid = KVPID(key, key)

        kvp_table[kvpid] = data
        self.assertIn(kvpid, kvp_table)

        future = self.nc[0].join_network(self.nc[1].address)

        self.assertTrue(future.result())

        future = self.nc[0].find_value_from_node(self.nc[1].node, key)
        find_value_result = future.result()

        self.assertIsInstance(find_value_result, FindValueFromNodeResult)
        self.assertEqual(len(data), find_value_result.kvp_info_list[0].size)

    def test_get_value_from_other_node(self):
        '''It should download the value from the other node'''

        self.setup_nodes(2)

        data = b'\x00\x01\x03' * 500
        key = KeyBytes(hashlib.sha1(data).digest())
        kvp_table = MemoryKVPTable()
        self.nc[1]._kvp_table = kvp_table
        kvpid = KVPID(key, key)

        kvp_table[kvpid] = data
        self.assertIn(kvpid, kvp_table)

        future = self.nc[0].join_network(self.nc[1].address)

        self.assertTrue(future.result())

        read_transfer_task = self.nc[0].get_value_from_node(self.nc[1].node,
            key)

        f = read_transfer_task.result()
        test_data = f.read()

        self.stop_event_reactors()
        self.join_event_reactors()

        self.assertTrue(data, test_data)

    def test_store_to_node(self):
        '''It should store the data to another node'''

        self.setup_nodes(2)

        data = b'\x00\x01\x03' * 500
        key = KeyBytes(hashlib.sha1(data).digest())
        kvp_table = MemoryKVPTable()
        self.nc[1]._kvp_table = kvp_table
        kvpid = KVPID(key, key)

        future = self.nc[0].join_network(self.nc[1].address)

        self.assertTrue(future.result())

        store_to_node_task = self.nc[0].store_to_node(self.nc[1].node,
            key, key, data, 12345678)

        self.assertEqual(len(data), store_to_node_task.result())

        # FIXME: once download status mechanism exists, fix sleep
        time.sleep(0.1)
        self.assertIn(kvpid, kvp_table)

        store_to_node_task = self.nc[0].store_to_node(self.nc[1].node,
            key, key, data, 12345678)

        self.assertEqual(0, store_to_node_task.result())

        self.stop_event_reactors()
        self.join_event_reactors()
