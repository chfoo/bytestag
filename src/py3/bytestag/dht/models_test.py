from bytestag.dht.models import NodeList, KVPExchangeInfoList, KVPExchangeInfo
from bytestag.dht.tables import Node
from bytestag.keys import KeyBytes
import unittest


class TestNodeList(unittest.TestCase):
    def test_josn_support(self):
        '''It should convert to json and back'''

        node_list = NodeList([Node(KeyBytes(), ('127.0.0.1', 12345))])

        self.assertEqual(node_list,
            NodeList.from_json_loadable(node_list.to_json_dumpable()))


class TestKVPExchangeInfoList(unittest.TestCase):
    def test_josn_support(self):
        '''It should convert to json and back'''

        kvp_info_list = KVPExchangeInfoList(
            [KVPExchangeInfo(KeyBytes(), KeyBytes(), 123, 456)])

        self.assertEqual(kvp_info_list,
            KVPExchangeInfoList.from_json_loadable(
                kvp_info_list.to_json_dumpable()))


class TestKVPExchangeInfo(unittest.TestCase):
    def test_json_support(self):
        '''It should convert to json and back'''

        kvp_info = KVPExchangeInfo(KeyBytes(), KeyBytes(), 1234, 123456789)

        self.assertEqual(kvp_info,
            KVPExchangeInfo.from_json_loadable(kvp_info.to_json_dumpable()))
