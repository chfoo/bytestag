'''Tables test'''
from bytestag.dht.tables import Node, RoutingTable, Bucket, BucketFullError
from bytestag.keys import KeyBytes
import logging
import os
import random
import unittest

_logger = logging.getLogger(__name__)


class TestRoutingTable(unittest.TestCase):
    def test_node_equality(self):
        '''It should be equal if the node's id and address are equal'''

        contact1 = Node(KeyBytes('3E4FF22E9E8B92CFCEBC10D8445EB3DE85D93DB9'),
            ('10.0.0.0', 8000))
        contact2 = Node(KeyBytes('3E4FF22E9E8B92CFCEBC10D8445EB3DE85D93DB9'),
            ('10.0.0.0', 8000))
        contact3 = Node(KeyBytes('3E4FF22E9E8B92CFCEBC10D8445EB3DE85D93DB9'),
            ('192.0.0.0', 8000))

        self.assertEqual(contact1, contact2)
        self.assertNotEqual(contact1, contact3)

    def test_node_in_container(self):
        '''It should return that the node is in the list with two instances
        of Node with same id and address'''

        contact1 = Node(KeyBytes('3E4FF22E9E8B92CFCEBC10D8445EB3DE85D93DB9'),
            ('10.0.0.0', 8000))
        contact2 = Node(KeyBytes('3E4FF22E9E8B92CFCEBC10D8445EB3DE85D93DB9'),
            ('10.0.0.0', 8000))

        l = [contact1]

        self.assertTrue(contact2 in l)

    def test_add_node(self):
        '''It should add a node'''

        node = Node(KeyBytes(), ('10.0.0.0', 8000))
        rt = RoutingTable()

        rt.node_update(node)
        self.assertTrue(node in rt)

    def test_full_bucket(self):
        '''It should raise exception when the 8th bucket is full'''

        rt = RoutingTable()

        for i in range(Bucket.MAX_BUCKET_SIZE + 1):
            key = KeyBytes(b'\x00' \
                + os.urandom(KeyBytes.BIT_SIZE // 8 - 1))
            node = Node(key,
                ('10.0.0.0', random.randint(1024, 10000)))

            if i == 20:
                self.assertRaises(BucketFullError, rt.node_update, node)
            else:
                rt.node_update(node)

    def test_add_self(self):
        '''It should not add a Node with a KeyBytes that is ours'''

        key = KeyBytes()
        rt = RoutingTable(key=key)
        node = Node(key, ('10.0.0.0', 1234))

        self.assertRaises(ValueError, rt.node_update, node)
        self.assertFalse(node in rt)
