
from bytestag.keys import KeyBytes
from bytestag.storage import (MemoryKVPTable, DatabaseKVPTable,
    SharedFilesKVPTable)
from bytestag.tables import KVPID
import bytestag.storage
import hashlib
import logging
import os.path
import random
import tempfile
import time
import unittest


_logger = logging.getLogger(__name__)


class TestFunctions(unittest.TestCase):
    SIZE = 1024

    def test_part_to_byte_number(self):
        '''It should map part numbers to offsets in files'''

        self.assertEqual(bytestag.storage.part_to_byte_number(0, self.SIZE),
            0)
        self.assertEqual(bytestag.storage.part_to_byte_number(1, self.SIZE),
            1024)
        self.assertEqual(bytestag.storage.part_to_byte_number(12, self.SIZE),
            12288)

    def test_byte_to_part_number(self):
        '''It should map bytes to part numbers'''

        self.assertEqual(bytestag.storage.byte_to_part_number(0, self.SIZE),
            0)
        self.assertEqual(bytestag.storage.byte_to_part_number(1, self.SIZE),
            0)
        self.assertEqual(bytestag.storage.byte_to_part_number(1023, self.SIZE),
            0)
        self.assertEqual(bytestag.storage.byte_to_part_number(1024, self.SIZE),
            1)
        self.assertEqual(bytestag.storage.byte_to_part_number(1025, self.SIZE),
            1)

    def test_total_parts(self):
        '''It should give the upperbound of parts needed'''

        self.assertEqual(bytestag.storage.total_parts(0, self.SIZE),
            0)
        self.assertEqual(bytestag.storage.total_parts(1, self.SIZE),
            1)
        self.assertEqual(bytestag.storage.total_parts(1023, self.SIZE),
            1)
        self.assertEqual(bytestag.storage.total_parts(1024, self.SIZE),
            1)
        self.assertEqual(bytestag.storage.total_parts(1025, self.SIZE),
            2)


class TableMixin(object):
    def table_store_get(self, data, kvp_table):
        kvpid = KVPID(KeyBytes(), KeyBytes.new_hash(data))

        self.assertFalse(kvpid in kvp_table)

        kvp_table[kvpid] = data

        self.assertTrue(kvpid in kvp_table)
        self.assertTrue(kvp_table.indices(kvpid.key))

        record = kvp_table.record(kvpid)

        self.assertEqual(len(data), record.size)

        del kvp_table[kvpid]

        self.assertFalse(kvpid in kvp_table)


class TestMemoryKVPTable(unittest.TestCase, TableMixin):
    def test_store_get(self):
        '''It should store and get'''

        data = b'kitteh' * 100
        kvp_table = MemoryKVPTable()

        self.table_store_get(data, kvp_table)


class TestDatabaseKVPTable(unittest.TestCase, TableMixin):
    def test_store_get(self):
        '''It should store and get'''

        temp_dir = tempfile.TemporaryDirectory()
        path = os.path.join(temp_dir.name, 'test.db')
        data = b'kitteh' * 100
        kvp_table = DatabaseKVPTable(path)

        self.table_store_get(data, kvp_table)


class TestSharedFilesKVPTable(unittest.TestCase, TableMixin):
    def create_file(self, path):
        with open(path, 'wb') as f:
            f.write(os.urandom(random.randint(0, 10000)))

    def test_hash(self):
        '''It should hash the files in each directory'''

        shared_dir = tempfile.TemporaryDirectory()
        data1 = os.urandom(4) + b'\x00' * 1000
        data2 = os.urandom(4) + b'\x00' * 1000
        hash1 = hashlib.sha1(data1).digest()
        hash2 = hashlib.sha1(data2).digest()

        with open(os.path.join(shared_dir.name, 'a.txt'), 'wb') as f:
            f.write(data1)

        with open(os.path.join(shared_dir.name, 'b.txt'), 'wb') as f:
            f.write(data2)

        temp_dir = tempfile.TemporaryDirectory()
        path = os.path.join(temp_dir.name, 'test.db')
        kvp_table = SharedFilesKVPTable(path)

        kvp_table.shared_directories.append(shared_dir.name)

        task = kvp_table.hash_directories()
        task.result()

        self.assertIn(KVPID(KeyBytes(hash1), KeyBytes(hash1)), kvp_table)
        self.assertIn(KVPID(KeyBytes(hash2), KeyBytes(hash2)), kvp_table)

        data2 = os.urandom(4) + b'\x00' * 1000
        data3 = os.urandom(4) + b'\x00' * 1000

        # XXX: Delay for integer filesystem timestamps
        time.sleep(1)

        os.remove(os.path.join(shared_dir.name, 'a.txt'))

        with open(os.path.join(shared_dir.name, 'b.txt'), 'wb') as f:
            f.write(data2)

        with open(os.path.join(shared_dir.name, 'c.txt'), 'wb') as f:
            f.write(data3)

        hash2 = hashlib.sha1(data2).digest()
        hash3 = hashlib.sha1(data3).digest()

        task = kvp_table.hash_directories()
        task.result()

#        # Row factory is None due to python bug #15545
#        with kvp_table._connection(row_factory=None) as con:
#            for line in con.iterdump():
#                print(line)
#
#        raise Exception('test')

        self.assertNotIn(KVPID(KeyBytes(hash1), KeyBytes(hash1)), kvp_table)
        self.assertIn(KVPID(KeyBytes(hash2), KeyBytes(hash2)), kvp_table)
        self.assertIn(KVPID(KeyBytes(hash3), KeyBytes(hash3)), kvp_table)
