'''Models JSON serializatin'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from bytestag.dht.tables import Node
from bytestag.keys import KeyBytes
import collections
import json
import logging

__docformat__ = 'restructuredtext en'
_logger = logging.getLogger(__name__)


class JSONKeys(object):
    '''JSON keys'''

    RPC = 'rpc'
    NETWORK_ID = 'netid'
    NODE_ID = 'nodeid'
    NODES = 'nodes'
    KEY = 'key'
    INDEX = 'index'
    VALUES = 'vals'
    SIZE = 'size'
    TRANSFER_ID = 'xferid'
    VALUE_OFFSET = 'valofs'
    TIMESTAMP = 'timestmp'

    class RPCs(object):
        PING = 'ping'
        STORE = 'store'
        FIND_NODE = 'findnode'
        FIND_VALUE = 'findval'
        GET_VALUE = 'getval'


class NodeList(list):
    '''A list of nodes

    JSON format
    ===========

    A node list is an array of objects.

    Each object must contain the host name, port number, and base64 encoded
    node ID.
    '''

    HOST = 'host'
    PORT = 'port'
    NODE_ID = 'id'

    @classmethod
    def from_json_loadable(cls, array):
        '''Return a node list

        :raise TypeError: Didn't get a ``dict``
        :raise ValueError: The list is invalid
        '''

        l = []

        if not isinstance(array, list):
            return TypeError('Not a list')

        for dict_obj in array:
            if not isinstance(dict_obj, dict):
                raise ValueError('Item is not a dict')

            host = dict_obj.get(NodeList.HOST)
            port = dict_obj.get(NodeList.PORT)
            node_id_str = dict_obj.get(NodeList.NODE_ID)

            if not isinstance(host, str):
                raise ValueError('Not a valid host')

            if not isinstance(port, int) or not (1 <= port <= 2 ** 16 - 1):
                raise ValueError('Not a valid port number')

            address = (host, port)
            key = KeyBytes(node_id_str)

            l.append(Node(key, address))

        return NodeList(l)

    def to_json_dumpable(self):
        '''Return a list of dict

        :rtype: ``list``
        '''

        node_list = []

        for node in self:
            node_list.append({
                NodeList.HOST: node.address[0],
                NodeList.PORT: node.address[1],
                NodeList.NODE_ID: node.key.base64,
            })

        return node_list

    def sort_distance(self, key):
        '''Sort inplace the list by distance to given key.

        The first item in the list is closest to the given key.
        '''

        self.sort(key=lambda node: node.key.distance_int(key))


class KVPExchangeInfo(collections.namedtuple('KVPExchangeInfo',
['key', 'index', 'size', 'timestamp'])):
    '''Description about a key-value used for storage decisions.'''

    __slots__ = ()
    KEY = 'key'
    INDEX = 'index'
    SIZE = 'size'
    TIMESTAMP = 'time'

    @classmethod
    def from_kvp_record(cls, kvp_record):
        return KVPExchangeInfo(kvp_record.key, kvp_record.index,
            kvp_record.size, kvp_record.timestamp)

    @classmethod
    def from_json_loadable(cls, dict_obj):
        if not isinstance(dict_obj, dict):
            raise TypeError('Not a dict')

        key = KeyBytes(dict_obj.get(KVPExchangeInfo.KEY, object))
        index = KeyBytes(dict_obj.get(KVPExchangeInfo.INDEX, object))
        size = dict_obj.get(KVPExchangeInfo.SIZE)
        timestamp = dict_obj.get(KVPExchangeInfo.TIMESTAMP)

        if size is None:
            pass
        elif not isinstance(size, int):
            raise ValueError('Size is not an int')
        else:
            size = int(size)

        if timestamp is None:
            pass
        elif not isinstance(timestamp, (int, float)):
            raise ValueError('Timestamp %s is not float')
        else:
            timestamp = float(timestamp)

        kvp_info = KVPExchangeInfo(key, index, size, timestamp)

        return kvp_info

    def to_json_dumpable(self):
        return {
            KVPExchangeInfo.KEY: self.key.base64,
            KVPExchangeInfo.INDEX: self.index.base64,
            KVPExchangeInfo.SIZE: self.size,
            KVPExchangeInfo.TIMESTAMP: self.timestamp,
        }


class KVPExchangeInfoList(list):
    '''A list of :class:`KVPExchangeInfo`'''

    @classmethod
    def from_kvp_record_list(cls, kvp_record_list):
        l = KVPExchangeInfoList()

        for kvp_record in kvp_record_list:
            l.append(KVPExchangeInfo(kvp_record.key, kvp_record.index,
            kvp_record.size, kvp_record.timestamp))

        return l

    @classmethod
    def from_json_loadable(cls, array):
        '''Return a node list

        :raise TypeError: Didn't get a ``dict``
        :raise ValueError: The list is invalid
        '''

        l = []

        if not isinstance(array, list):
            return TypeError('Not a list')

        for dict_obj in array:
            l.append(KVPExchangeInfo.from_json_loadable(dict_obj))

        return KVPExchangeInfoList(l)

    def to_json_dumpable(self):
        l = []

        for kvp_info in self:
            l.append(kvp_info.to_json_dumpable())

        return l


class FileHashInfo(object):
    '''Represents the hashes of a file and its parts.'''

    NAME = 'FileHashInfo'
    KEY_TYPE = '!'
    KEY_HASH = 'hash'
    KEY_PART_HASHES = 'parts'

    def __init__(self, file_hash, part_hashes):
        self._file_hash = KeyBytes(file_hash)
        self._part_hashes = list(map(KeyBytes, part_hashes))

    @classmethod
    def from_json_loadable(cls, o):
        dict_obj = json.loads(o)

        if not isinstance(dict_obj, dict):
            raise TypeError('Not a dict')

        file_hash = dict_obj[FileHashInfo.KEY_HASH]
        part_hashes = dict_obj[FileHashInfo.KEY_PART_HASHES]
        part_hashes = list(map(KeyBytes, part_hashes))

        return FileHashInfo(file_hash, part_hashes)

    @classmethod
    def from_bytes(cls, bytes_):
        return FileHashInfo.from_json_loadable(json.loads(bytes_.decode()))

    def to_json_dumpable(self):
        part_hashes = list([b.base64 for b in self._part_hashes])

        d = {
            FileHashInfo.KEY_TYPE: FileHashInfo.NAME,
            FileHashInfo.KEY_HASH: self._file_hash.base64,
            FileHashInfo.KEY_PART_HASHES: part_hashes,
        }

        return d

    def to_bytes(self):
        return json.dumps(self.to_json_dumpable(), sort_keys=True).encode()


class CollectionInfo(object):
    '''to be written'''

    # TODO:
    def __init__(self):
        pass

