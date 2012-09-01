'''Storage management and implementations of KVPTables'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from bytestag.dht.models import FileInfo
from bytestag.events import Task
from bytestag.keys import KeyBytes
from bytestag.tables import KVPTable, KVPRecord, KVPID
import collections
import contextlib
import hashlib
import itertools
import logging
import math
import os
import sqlite3
import threading

__docformat__ = 'restructuredtext en'
_logger = logging.getLogger(__name__)


def part_to_byte_number(part_number, part_size):
    '''Converts a file segment number to the byte offset

    :rtype: :obj:`int`
    '''

    return part_number * part_size


def byte_to_part_number(byte_number, part_size):
    '''Converts a byte offset to a file segment number.

    :rtype: :obj:`int`
    '''

    return byte_number // part_size


def total_parts(total_byte_size, part_size):
    '''Returns the total number of segments of a file

    :rtype: :obj:`int`
    '''

    return math.ceil(total_byte_size / part_size)


class MemoryKVPTable(KVPTable):
    '''A quick and dirty implementation of :class:`.KVPTable`

    .. note::
        This class is generally used for unit tests.
    '''

    def __init__(self):
        KVPTable.__init__(self)
        self._table = collections.defaultdict(
            lambda: collections.defaultdict(dict))

    def _contains(self, kvpid):
        return kvpid.index in self._table[kvpid.key]

    def indices(self, key):
        return list(self._table[key].keys())

    def _getitem(self, kvpid):
        return self._table[kvpid.key][kvpid.index]['value']

    def _setitem(self, kvpid, value):
        self._table[kvpid.key][kvpid.index]['value'] = value

    def _delitem(self, kvpid):
        del self._table[kvpid.key][kvpid.index]

    def keys(self):
        for key in self._table:
            for index in self._table[key]:
                yield KVPID(key, index)

    def record(self, kvpid):
        return MemoryKVPRecord(kvpid, self._table[kvpid.key][kvpid.index])

    def is_acceptable(self, kvpid, size, timestamp):
        if not kvpid in self:
            return True

        if self.record(kvpid).timestamp != timestamp:
            return True


class MemoryKVPRecord(KVPRecord):
    '''The record associated with :class:`MemoryKVPTable`'''

    def __init__(self, kvpid, d):
        self._kvpid = kvpid
        self._d = d

    @property
    def key(self):
        return self._kvpid.key

    @property
    def index(self):
        return self._kvpid.index

    @property
    def size(self):
        return len(self._d['value'])

    @property
    def value(self):
        return self._d['value']

    @property
    def timestamp(self):
        return self._d.get('timestamp')

    @timestamp.setter
    def timestamp(self, seconds):
        self._d['timestamp'] = seconds

    @property
    def time_to_live(self):
        return self._d.get('time_to_live')

    @time_to_live.setter
    def time_to_live(self, seconds):
        self._d['time_to_live'] = seconds

    @property
    def is_original(self):
        return self._d.get('is_original')

    @is_original.setter
    def is_original(self, b):
        self._d['is_original'] = b

    @property
    def last_update(self):
        return self._d.get('last_update')

    @last_update.setter
    def last_update(self, seconds):
        self._d['last_update'] = seconds


class SQLite3Mixin(object):
    '''A SQLite 3 mixin class to provide connection management'''

    @contextlib.contextmanager
    def connection(self):
        '''Return a connection context manager'''

        if not hasattr(self, '_num_connections'):
            self._num_connections = 0

#        if self._num_connections:
#            _logger.warning('There are %d connections already',
#                self._num_connections)

        con = sqlite3.connect(self._path, isolation_level='DEFERRED',
            detect_types=sqlite3.PARSE_DECLTYPES)
        con.row_factory = sqlite3.Row
        con.execute('PRAGMA synchronous=NORMAL')
        con.execute('PRAGMA journal_mode=WAL')
        con.execute('PRAGMA foreign_keys = ON')

        self._num_connections += 1
        _logger.debug('Begin transaction current=%d', self._num_connections)

        try:
            with con:
                yield con
        finally:
            self._num_connections -= 1

            _logger.debug('End transaction current=%d', self._num_connections)

    @property
    def database_size(self):
        '''The size of the database.

        :rtype: :obj:`int`
        '''

        with self.connection() as con:
            cur = con.execute('PRAGMA page_count')
            page_count = cur.fetchone()[0]
            cur = con.execute('PRAGMA page_size')
            page_size = cur.fetchone()[0]

        return page_count * page_size

    def iter_query(self, query, params=(), limit=1000):
        '''Return rows that are fetch in blocks and stored in memory.

        This function is useful for iterating the entire database without
        blocking other connections.
        '''

        offset = 0
        deque = collections.deque()

        while True:
            deque.clear()

            with self.connection() as con:
                cur = con.execute(query.format(limit, offset), params)

                for row in cur:
                    deque.append(row)

                if not deque:
                    break

            while True:
                try:
                    yield deque.popleft()
                except IndexError:
                    break

            offset += limit


class DatabaseKVPTable(KVPTable, SQLite3Mixin):
    '''A KVPTable stored as a SQLite database'''

    def __init__(self, path, max_size=2 ** 36):
        '''
        :param path: A filename to the database.
        :param max_size: The maximum database size that the table will grow.
        '''

        KVPTable.__init__(self)
        self._max_size = max_size
        self._path = path
        self._create_tables()

    @property
    def max_size(self):
        '''The maximum size the table will grow.'''
        return self._max_size

    @max_size.setter
    def max_size(self, s):
        self._max_size = s

    def _create_tables(self):
        with self.connection() as con:
            con.execute('CREATE TABLE IF NOT EXISTS kvps ('
                'key_id BLOB NOT NULL, index_id BLOB NOT NULL,'
                'timestamp INTEGER,'
                'time_to_live INTEGER,'
                'is_original INTEGER,'
                'value BLOB,'
                'last_update INTEGER DEFAULT 0,'
                'PRIMARY KEY (key_id, index_id))')

    def _getitem(self, kvpid):
        with self.connection() as con:
            cur = con.execute('SELECT value FROM kvps '
                'WHERE key_id = ? AND index_id = ? '
                'LIMIT 1', (kvpid.key, kvpid.index))

        for row in cur:
            return row['value']

    def _contains(self, kvpid):
        with self.connection() as con:
            cur = con.execute('SELECT 1 FROM kvps '
                'WHERE key_id = ? AND index_id = ? LIMIT 1',
                (kvpid.key, kvpid.index))

            return True if cur.fetchone() else False

    def _setitem(self, kvpid, value):
        with self.connection() as con:
            params = (value, kvpid.key, kvpid.index)

            try:
                con.execute('INSERT INTO kvps '
                    '(value, key_id, index_id) VALUES (?, ?, ?)', params)
            except sqlite3.IntegrityError:
                con.execute('UPDATE kvps SET value = ? '
                    'WHERE key_id = ? AND index_id = ?', params)

    def keys(self):
        query = 'SELECT key_id, index_id FROM kvps LIMIT {} OFFSET {}'

        for row in self.iter_query(query):
            yield KVPID(KeyBytes(row['key_id']), KeyBytes(row['index_id']))

    def indices(self, key):
        for row in self.iter_query('SELECT index_id FROM kvps WHERE '
        'key_id = ? LIMIT {} OFFSET {}', (key,)):
            yield KeyBytes(row['index_id'])

    def _delitem(self, kvpid):
        with self.connection() as con:
            con.execute('DELETE FROM kvps WHERE '
                'key_id = ? AND index_id = ?', (kvpid.key, kvpid.index))

    def is_acceptable(self, kvpid, size, timestamp):
        if kvpid in self and self.record(kvpid).timestamp == timestamp:
            return False

        if self.database_size + size > self._max_size:
            return False

        return True

    def record(self, kvpid):
        return DatabaseKVPRecord(self, kvpid)

    def clean(self):
        '''Remove expired key-value pairs.'''

        _logger.debug('Clean database')

        with self.connection() as con:
            con.execute('''DELETE FROM kvps WHERE '''
                '''timestamp + time_to_live < strftime('%s', 'now')''')


class DatabaseKVPRecord(KVPRecord):
    '''The record associated with :class:`DatabaseKVPTable`.'''

    __slots__ = ('_table', '_kvpid')

    def __init__(self, table, kvpid):
        self._table = table
        self._kvpid = kvpid

    def _get_field(self, name):
        with self._table.connection() as con:
            cur = con.execute('SELECT {} FROM kvps '
                'WHERE key_id = ? AND index_id = ?'.format(name),
                (self._kvpid.key, self._kvpid.index))

        for row in cur:
            return row[0]

    def _save_field(self, name, value):
        with self._table.connection() as con:
            con.execute('UPDATE kvps SET {} = ? '
                'WHERE key_id = ? AND index_id = ?'.format(name),
                (value, self._kvpid.key, self._kvpid.index))

    @property
    def key(self):
        return self._kvpid.key

    @property
    def index(self):
        return self._kvpid.index

    @property
    def value(self):
        return self._table[self._kvpid]

    @property
    def size(self):
        return len(self.value)

    @property
    def timestamp(self):
        return self._get_field('timestamp')

    @timestamp.setter
    def timestamp(self, seconds):
        self._save_field('timestamp', seconds)

    @property
    def time_to_live(self):
        return self._get_field('time_to_live')

    @time_to_live.setter
    def time_to_live(self, seconds):
        self._save_field('time_to_live', seconds)

    @property
    def is_original(self):
        return self._get_field('is_original')

    @is_original.setter
    def is_original(self, b):
        self._save_field('is_original', b)

    @property
    def last_update(self):
        return self._get_field('last_update')

    @last_update.setter
    def last_update(self, seconds):
        self._save_field('last_update', seconds)


class ReadOnlyTableError(Exception):
    '''This error is raised when the table does support storing values.'''
    pass


class CollectionInfoTypes(object):
    '''Types of CollectionInfo file types'''

    DUMMY, BYTESTAG, BITTORRENT = range(3)
    BYTESTAG_COOKIE = b'{"!":"BytestagCollectionInfo"'


class SharedFilesKVPTable(KVPTable, SQLite3Mixin):
    '''Provides a KVPTable interface to shared files split into pieces.'''

    def __init__(self, path):
        '''
        :param path: The filename of the database.
        '''

        KVPTable.__init__(self)
        self._path = path
        self._shared_directories = []
        self._create_tables()

    def _create_tables(self):
        with self.connection() as con:
            con.execute('CREATE TABLE IF NOT EXISTS files ('
                'id INTEGER PRIMARY KEY,'
                'filename TEXT NOT NULL UNIQUE,'
                'key BLOB NOT NULL,'
                '`index` BLOB NOT NULL,'
                'size INTEGER NOT NULL,'
                'mtime INTEGER NOT NULL,'
                'part_size INTEGER NOT NULL,'
                'last_update INTEGER DEFAULT 0,'
                'file_hash_info BLOB NOT NULL)'
            )
            con.execute('CREATE TABLE IF NOT EXISTS parts ('
                'hash_id BLOB PRIMARY KEY,'
                'file_id INTEGER NOT NULL,'
                'file_offset INTEGER NOT NULL,'
                'last_update INTEGER DEFAULT 0,'
                'FOREIGN KEY (file_id) REFERENCES files (id)'
                'ON DELETE CASCADE'
                ')')
            con.execute('CREATE TABLE IF NOT EXISTS collections ('
                'file_id INTEGER PRIMARY KEY,'
                'type INTEGER NOT NULL,'
                'FOREIGN KEY (file_id) REFERENCES files (id)'
                'ON DELETE CASCADE'
                ')')
            con.execute('CREATE INDEX IF NOT EXISTS key ON files (key)')

    @property
    def shared_directories(self):
        '''A list directories to be shared.

        Modify the list at your will, but be sure to sure to call
        :func:`hash_directories` as file monitoring is not yet supported.
        '''

        return self._shared_directories

    def is_acceptable(self, kvpid, size, timestamp):
        return False

    def indices(self, key):
        if self._contains_part(key):
            yield key

        for i in self._file_hash_index(key):
            yield i

    def _file_hash_index(self, key):
        for row in self.iter_query('SELECT `index` FROM files '
        'WHERE key = ?', (key,)):

            yield KeyBytes(row['index'])

    def _contains(self, kvpid):
        if kvpid.key == kvpid.index:
            return self._contains_part(kvpid.key)

        return self._contains_file_hash_info(kvpid)

    def _contains_part(self, key):
        with self.connection() as con:
            cur = con.execute('SELECT 1 FROM parts WHERE '
                'hash_id = ? ', (key,))
            row = cur.fetchone()

            if row:
                return True

    def _contains_file_hash_info(self, kvpid):
        with self.connection() as con:
            cur = con.execute('SELECT 1 FROM files WHERE '
                'key = ? AND `index` = ? ', (kvpid.key, kvpid.index))
            row = cur.fetchone()

            if row:
                return True

    def keys(self):
        return itertools.chain(self._parts_keys(), self._files_keys())

    def _parts_keys(self):
        query = 'SELECT hash_id FROM parts LIMIT {} OFFSET {}'

        for row in self.iter_query(query):
            yield KVPID(KeyBytes(row[0]), KeyBytes(row[0]))

    def _files_keys(self):
        query = 'SELECT key, `index` FROM files LIMIT {} OFFSET {}'

        for row in self.iter_query(query):
            yield KVPID(KeyBytes(row[0]), KeyBytes(row[1]))

    def _getitem(self, kvpid):
        if kvpid.key == kvpid.index:
            return self._get_part(kvpid.key)
        else:
            return self._get_file_hash_info(kvpid)

    def _get_part(self, key):
        with self.connection() as con:
            cur = con.execute('SELECT files.filename,'
                'parts.file_offset, files.part_size '
                'FROM parts JOIN files '
                'ON parts.file_id = files.id '
                'WHERE hash_id = ?', (key,))

            filename, offset, part_size = cur.fetchone()

        with open(filename, 'rb') as f:
            f.seek(offset)

            return f.read(part_size)

    def file_hash_info(self, kvpid):
        return FileInfo.from_bytes(self._get_file_hash_info(kvpid))

    def _get_file_hash_info(self, kvpid):
        with self.connection() as con:
            cur = con.execute('SELECT file_hash_info FROM files '
                'WHERE key = ? AND `index` = ? LIMIT 1',
                (kvpid.key, kvpid.index))

            for row in cur:
                return row['file_hash_info']

        raise IndexError('Not found')

    def _delitem(self, kvpid):
        raise ReadOnlyTableError()

    def _setitem(self, kvpid, value):
        raise ReadOnlyTableError()

    def record(self, kvpid):
        if kvpid.key == kvpid.index:
            return SharedFilesRecord(self, kvpid)
        else:
            return SharedFileHashRecord(self, kvpid)

    def hash_directories(self):
        '''Hash the directories and populate the table with file info.

        :rtype: :class:`SharedFilesHashTask`
        '''

        task = SharedFilesHashTask(self)

        thread = threading.Thread(target=task)
        thread.daemon = True
        thread.name = 'SharedFilesHashTask'
        thread.start()

        return task

    @property
    def num_files(self):
        with self.connection() as con:
            cur = con.execute('SELECT COUNT(1) FROM files')

            return cur.fetchone()[0]

    @property
    def num_collections(self):
        with self.connection() as con:
            cur = con.execute('SELECT COUNT(1) FROM collections')

            return cur.fetchone()[0]

    @property
    def total_disk_size(self):
        with self.connection() as con:
            cur = con.execute('SELECT SUM(size) FROM files')

            return cur.fetchone()[0]


class SharedFilesRecord(KVPRecord):
    '''The record associated with :class:`SharedFilesKVPTable`.

    This record describes a single file on the filesystem.

    :see: :class:`SharedFileHashRecord`
    '''

    __slots__ = ('_table', '_kvpid')

    def __init__(self, table, kvpid):
        self._table = table
        self._kvpid = kvpid

    def _get_field(self, name):
        with self._table.connection() as con:
            cur = con.execute('SELECT {} FROM parts '
                'WHERE hash_id = ?'.format(name),
                (self._kvpid.key,))

            for row in cur:
                return row[0]

    def _save_field(self, name, value):
        with self._table.connection() as con:
            con.execute('UPDATE parts SET {} = ? '
                'WHERE hash_id = ?'.format(name),
                (value, self._kvpid.key))

    @property
    def key(self):
        return self._kvpid.key

    @property
    def index(self):
        return self._kvpid.index

    @property
    def value(self):
        return self._table[self._kvpid]

    @property
    def size(self):
        return len(self.value)

    @property
    def timestamp(self):
        return self.last_update

    @timestamp.setter
    def timestamp(self, seconds):
        raise ReadOnlyTableError()

    @property
    def time_to_live(self):
        return None

    @time_to_live.setter
    def time_to_live(self, seconds):
        raise ReadOnlyTableError()

    @property
    def is_original(self):
        return True

    @is_original.setter
    def is_original(self, b):
        raise ReadOnlyTableError()

    @property
    def last_update(self):
        return self._get_field('last_update')

    @last_update.setter
    def last_update(self, seconds):
        self._save_field('last_update', seconds)


class SharedFileHashRecord(KVPRecord):
    '''The record associated with :class:`SharedFilesKVPTable`.

    This record describes a single file on the filesystem.

    :see: :class:`SharedFileRecord`
    '''

    __slots__ = ('_table', '_kvpid')

    def __init__(self, table, kvpid):
        self._table = table
        self._kvpid = kvpid

    def _get_field(self, name):
        with self._table.connection() as con:
            cur = con.execute('SELECT {} FROM files '
                'WHERE key = ? and `index` = ?'.format(name),
                (self._kvpid.key, self._kvpid.index))

        for row in cur:
            return row[0]

    def _save_field(self, name, value):
        with self._table.connection() as con:
            con.execute('UPDATE files SET {} = ? '
                'WHERE key = ? AND `index` = ?'.format(name),
                (value, self._kvpid.key, self._kvpid.index))

    @property
    def key(self):
        return self._kvpid.key

    @property
    def index(self):
        return self._kvpid.index

    @property
    def value(self):
        return self._table[self._kvpid]

    @property
    def size(self):
        return len(self.value)

    @property
    def timestamp(self):
        return None

    @timestamp.setter
    def timestamp(self, seconds):
        raise ReadOnlyTableError()

    @property
    def time_to_live(self):
        return None

    @time_to_live.setter
    def time_to_live(self, seconds):
        raise ReadOnlyTableError()

    @property
    def is_original(self):
        return True

    @is_original.setter
    def is_original(self, b):
        raise ReadOnlyTableError()

    @property
    def last_update(self):
        return self._get_field('last_update')

    @last_update.setter
    def last_update(self, seconds):
        self._save_field('last_update', seconds)

    @property
    def file_hash_info(self):
        return self._table.file_hash_info(self._kvpid)


class SharedFilesHashTask(Task):
    '''A task that hashes and populates a shared files table.

    :ivar progress: a tuple (`str`, `int`) describing the filename and bytes
        read.
    '''

    def _walk_dir(self, path):
        '''Walk a directory in a sorted order and yield path, size and mtime'''

        # TODO: may run into recursion
        for dirpath, dirnames, filenames in os.walk(path, followlinks=True):
            dirnames.sort()

            for filename in sorted(filenames):
                file_path = os.path.join(dirpath, filename)
                size = os.path.getsize(file_path)
                mtime = int(os.path.getmtime(file_path))

                yield file_path, size, mtime

    def run(self, table, part_size=2 ** 18):
        self._table = table
        self._part_size = part_size

        for directory in table.shared_directories:
            if not self.is_running:
                return

            self._hash_directory(directory)

        if not table.shared_directories:
            _logger.info('No directories to hash')

        self._clean_database()

        self._table.value_changed_observer(None)

    def _hash_directory(self, directory):
        _logger.info('Hashing directory %s', directory)

        for file_path, size, mtime in self._walk_dir(directory):
            if not self.is_running:
                return

            if os.path.isfile(file_path):
                self._hash_file(file_path, size, mtime)

    def _hash_file(self, path, size, mtime):
        self.progress = (path, 0)

        with self._table.connection() as con:
            cur = con.execute('SELECT id, size, mtime '
                'FROM files WHERE '
                'filename = ? LIMIT 1', (path,))

            for row in cur:
                id_, result_size, result_mtime = row

                if result_size == size and result_mtime == mtime:
                    return

                con.execute('PRAGMA foreign_keys = ON')
                con.execute('DELETE FROM files WHERE id = ?', (id_,))

        self._hash_parts(path, size, mtime)

    def _hash_parts(self, path, size, mtime):
        _logger.info('Hashing file %s', path)

        whole_file_hasher = hashlib.sha1()
        hashes = []

        with open(path, 'rb') as f:
            while True:
                if not self.is_running:
                    return

                data = f.read(self._part_size)

                if not data:
                    break

                self.progress = (path, f.tell())

                whole_file_hasher.update(data)
                part_hasher = hashlib.sha1(data)
                hashes.append(part_hasher.digest())

        file_hash = whole_file_hasher.digest()
        file_hash_info = FileInfo(file_hash, hashes)
        index = hashlib.sha1(file_hash_info.to_bytes()).digest()

        with self._table.connection() as con:
            cur = con.execute('INSERT INTO files '
                '(key, `index`, size, mtime, part_size, filename,'
                'file_hash_info) '
                'VALUES (?, ? , ? , ? , ?, ?, ?)', (file_hash, index,
                    size, mtime, self._part_size, path,
                    file_hash_info.to_bytes()))

            row_id = cur.lastrowid

            for i in range(len(hashes)):
                offset = i * self._part_size
                hash_bytes = hashes[i]
                self.progress = (path, offset)

                try:
                    con.execute('INSERT INTO parts '
                        '(hash_id, file_id, file_offset) VALUES '
                    '(?, ?, ?)', (hash_bytes, row_id, offset))
                except sqlite3.IntegrityError:
                    _logger.exception('Possible duplicate')

            collection_type = self._get_collection_type(path)

            if collection_type:
                con.execute('INSERT INTO collections '
                    '(file_id, type) VALUES '
                    '(?, ?)', (row_id, collection_type))

    def _get_collection_type(self, path):
        cookie_len = len(CollectionInfoTypes.BYTESTAG_COOKIE)

        with open(path, 'rb') as f:
            data = f.read(cookie_len)

            if data.startswith(CollectionInfoTypes.BYTESTAG_COOKIE):
                return CollectionInfoTypes.BYTESTAG

            if path.endswith('.torrent'):
                f.seek(0)

                if self._check_bittorrent_file_contents(f):
                    return CollectionInfoTypes.BITTORRENT

    def _check_bittorrent_file_contents(self, f):
        data = f.read(1024)

        if b'info' in data and b'pieces' in data:
            return True

    def _clean_database(self):
        _logger.info('Cleaning database')

        delete_params = []

        with self._table.connection() as con:
            cur = con.execute('SELECT rowid, filename FROM files')

            for row in cur:
                rowid, filename = row

                if not os.path.exists(filename) \
                or not self._is_in_shared_directory(filename):
                    delete_params.append((rowid,))

        with self._table.connection() as con:
            con.execute('PRAGMA foreign_keys = ON')
            cur = con.executemany('DELETE FROM files WHERE rowid = ?',
                delete_params)

    def _is_in_shared_directory(self, path):
        for shared_dir in self._table._shared_directories:
            common_prefix = os.path.commonprefix([shared_dir, path])

            if common_prefix in self._table._shared_directories:
                return True
