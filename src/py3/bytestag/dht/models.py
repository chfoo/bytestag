'''Models JSON serializatin'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from bytestag.dht.tables import Node
from bytestag.keys import KeyBytes
import abc
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


class JSONDumpable(metaclass=abc.ABCMeta):
    @abc.abstractclassmethod
    def from_json_loadable(cls, o):  # @NoSelf
        pass

    @abc.abstractmethod
    def to_json_dumpable(self):
        pass


class Serializable(JSONDumpable):
    @classmethod
    def from_bytes(cls, bytes_):
        return cls.from_json_loadable(json.loads(bytes_.decode()))

    def to_bytes(self):
        return json.dumps(self.to_json_dumpable(), False, True, True, True,
            None, None, (',', ':'), None, sort_keys=True).encode()


class NodeList(list, JSONDumpable):
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
['key', 'index', 'size', 'timestamp']), JSONDumpable):
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


class KVPExchangeInfoList(list, JSONDumpable):
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


class FileInfo(Serializable):
    '''Represents the hashes of a file and its parts.'''

    HEADER = 'BytestagFileInfo'
    HASH = 'hash'
    PART_HASHES = 'parts'
    SIZE = 'size'
    FILENAME = 'filename'
    __slots__ = ('_file_hash', '_part_hashes', '_filename')

    def __init__(self, file_hash, part_hashes, size=None, filename=None):
        self._file_hash = None
        self._part_hashes = None
        self._size = None
        self._filename = None

        self.file_hash = file_hash
        self.part_hashes = part_hashes
        self.size = size
        self.filename = filename

    @property
    def file_hash(self):
        return self._file_hash

    @file_hash.setter
    def file_hash(self, bytes_):
        if not isinstance(bytes_, bytes):
            raise TypeError('Expected bytes, got {}')

        self._file_hash = KeyBytes(bytes_)

    @property
    def part_hashes(self):
        return self._part_hashes

    @part_hashes.setter
    def part_hashes(self, hashes):
        hashes[0]

        for hash_ in hashes:
            if not isinstance(hash_, bytes):
                raise TypeError('Expected bytes')

        self._part_hashes = list(map(KeyBytes, hashes))

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, o):
        if o is None:
            self._size = None
        elif not isinstance(o, int):
            raise TypeError('Expected int')
        elif o < 0:
            raise ValueError('Size cannot be negative')

        self._size = o

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, o):
        if o is None:
            self._filename = None
            return

        o[0]

        for name in o:
            if not isinstance(name, str):
                raise TypeError('Expected str')

        self._filename = o

    @classmethod
    def from_json_loadable(cls, d):
        return FileInfo(
            KeyBytes(d[FileInfo.HASH]),
            list(map(KeyBytes, d[FileInfo.PART_HASHES])),
            d.get(FileInfo.SIZE),
            d.get(FileInfo.FILENAME),
        )

    def to_json_dumpable(self):
        d = {
            '!': FileInfo.HEADER,
            FileInfo.HASH: self._file_hash.base64,
            FileInfo.PART_HASHES: list(b.base64 for b in self._part_hashes),
        }

        if self._filename:
            d[FileInfo.FILENAME] = self._filename

        if self._size:
            d[FileInfo.SIZE] = self._size

        return d


class CollectionInfo(Serializable):
    '''Represents a collection of file infos'''

    HEADER = 'BytestagCollectionInfo'
    FILES = 'files'
    COMMENT = 'comment'
    TIMESTAMP = 'timestamp'
    __slots__ = ('_file_infos', '_comment', '_timestamp')

    def __init__(self, file_infos, comment=None, timestamp=None):
        self._file_infos = None
        self._comment = None
        self._timestamp = None

        self.file_infos = file_infos
        self.comment = comment
        self.timestamp = timestamp

    @property
    def file_infos(self):
        return self._file_infos

    @file_infos.setter
    def file_infos(self, file_infos):
        file_infos[0]

        for file_info in file_infos:
            if not isinstance(file_info, FileInfo):
                raise TypeError('Expected FileInfo')

        self._file_infos = file_infos

    @property
    def comment(self):
        return self._comment

    @comment.setter
    def comment(self, comment):
        if not isinstance(comment, str) and comment is not None:
            raise TypeError('Expected str or None')

        self._comment = comment

    @property
    def timestamp(self):
        return self._timestamp

    @timestamp.setter
    def timestamp(self, timestamp):
        if timestamp is None:
            self._timestamp = timestamp
        elif not isinstance(timestamp, int):
            raise TypeError('Expected int')
        elif timestamp < 0:
            raise ValueError('timestamp must not be negative')

        self._timestamp = timestamp

    @classmethod
    def from_json_loadable(cls, d):
        return CollectionInfo(
            list(map(FileInfo.from_json_loadable, d[CollectionInfo.FILES])),
            d.get(CollectionInfo.COMMENT),
            d.get(CollectionInfo.TIMESTAMP)
        )

    def to_json_dumpable(self):
        files = list([i.to_json_dumpable() for i in self._file_infos])

        d = {
            '!': CollectionInfo.HEADER,
            CollectionInfo.FILES: files
        }

        if self._comment:
            d[CollectionInfo.COMMENT] = self._comment

        if self._timestamp:
            d[CollectionInfo.TIMESTAMP] = self._timestamp

        return d
