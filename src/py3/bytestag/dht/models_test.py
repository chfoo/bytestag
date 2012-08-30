from bytestag.dht.models import (NodeList, KVPExchangeInfoList, KVPExchangeInfo,
    FileInfo, CollectionInfo)
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


class TestFileInfo(unittest.TestCase):
    def test_read_json(self):
        '''It should read in a json with basic info'''

        s = (b'{'
            b'"!":"BytestagFileInfo",'
            b'"hash":"jbip9t8iC9lEz3jndkm5I2fTWV0=",'
            b'"parts":["jbip9t8iC9lEz3jndkm5I2fTWV0="]'
        b'}')

        info = FileInfo.from_bytes(s)

        self.assertEqual(info.file_hash,
            KeyBytes('jbip9t8iC9lEz3jndkm5I2fTWV0='))
        self.assertEqual(info.part_hashes,
            [KeyBytes('jbip9t8iC9lEz3jndkm5I2fTWV0=')])

        result_bytes = info.to_bytes()

        self.assertEqual(s, result_bytes)

    def test_read_json_extended(self):
        '''It should read in a json with extended info'''

        s = (b'{'
            b'"!":"BytestagFileInfo",'
            b'"filename":["my_file.txt"],'
            b'"hash":"jbip9t8iC9lEz3jndkm5I2fTWV0=",'
            b'"parts":["jbip9t8iC9lEz3jndkm5I2fTWV0="],'
            b'"size":123'
        b'}')

        info = FileInfo.from_bytes(s)

        self.assertEqual(info.file_hash,
            KeyBytes('jbip9t8iC9lEz3jndkm5I2fTWV0='))
        self.assertEqual(info.part_hashes,
            [KeyBytes('jbip9t8iC9lEz3jndkm5I2fTWV0=')])
        self.assertEqual(info.size, 123)
        self.assertEqual(info.filename, ['my_file.txt'])

        result_bytes = info.to_bytes()

        self.assertEqual(s, result_bytes)


class TestCollectionInfo(unittest.TestCase):
    def test_read_json(self):
        '''It should read in json with basic info'''

        s = (b'{'
            b'"!":"BytestagCollectionInfo",'
            b'"files":['
                b'{'
                b'"!":"BytestagFileInfo",'
                b'"hash":"jbip9t8iC9lEz3jndkm5I2fTWV0=",'
                b'"parts":["jbip9t8iC9lEz3jndkm5I2fTWV0="]'
                b'}'
            b']'
        b'}')

        info = CollectionInfo.from_bytes(s)

        self.assertIsInstance(info.file_infos[0], FileInfo)

        result_bytes = info.to_bytes()

        self.assertEqual(s, result_bytes)
