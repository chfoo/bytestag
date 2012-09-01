'''Specialized queues'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from bytestag.events import asynchronous
import atexit
import contextlib
import os.path
import pickle
import queue
import sqlite3
import tempfile
import threading

__docformat__ = 'restructuredtext en'


class BigDiskQueue(object):
    '''A queue that spools onto disk when needed.

    The core functionality is similar to :class:`queue.Queue`.
    '''

    def __init__(self, memory_size=100):
        self._queue = queue.Queue(memory_size)
        self._event = threading.Event()
        self._tables_created = False

        self._loop()

    @contextlib.contextmanager
    def _connection(self):
        con = sqlite3.connect(self._path, isolation_level='DEFERRED',
            detect_types=sqlite3.PARSE_DECLTYPES)
        con.row_factory = sqlite3.Row
        con.execute('PRAGMA synchronous=OFF')
        con.execute('PRAGMA journal_mode=WAL')
        # con.execute('PRAGMA foreign_keys = ON')

        with con:
            yield con

    def _create_tables(self):
        self._tables_created = True
        self._temp_dir = tempfile.TemporaryDirectory(suffix='-queue')
        self._path = os.path.join(self._temp_dir.name, 'queue.db')

        # FIXME: tempdir isn't being cleaned, perhaps problem with threads
        atexit.register(self._temp_dir.cleanup)

        with self._connection() as con:
            con.execute('CREATE TABLE IF NOT EXISTS queue '
                '(id INTEGER PRIMARY KEY, pickle BLOB NOT NULL)')

    def put(self, item, block=None, timeout=None):
        '''Put an item on the queue.

        This function is nonblocking. Parameters are provided for
        compatibility with :class:`queue.Queue`.
        '''

        try:
            self._queue.put_nowait(item)
        except queue.Full:
            if not self._tables_created:
                self._create_tables()

            self._put_database(item)

    def put_nowait(self, item):
        '''Put an item on the queue.'''
        return self.put(item, False)

    def get(self, block=True, timeout=None):
        '''Get an item from the queue.'''

        item = self._queue.get(block, timeout)

        if self._tables_created:
            self._event.set()

        return item

    def get_nowait(self):
        '''Get an item from the queue without blocking.'''

        return self.get(False)

    def _put_database(self, item):
        data = pickle.dumps(item)

        with self._connection() as con:
            con.execute('INSERT INTO queue (pickle) VALUES (?)', (data,))

    @asynchronous(name='BigDiskQueue loop')
    def _loop(self):
        while True:
            self._event.wait()
            self._event.clear()
            row_id = None

            with self._connection() as con:
                cur = con.execute('SELECT id, pickle FROM queue LIMIT 1')

                for row in cur:
                    item = pickle.loads(row['pickle'])
                    row_id = row['id']

            if not row_id:
                continue

            try:
                self._queue.put_nowait(item)
            except queue.Full:
                continue
            else:
                with self._connection() as con:
                    con.execute('DELETE FROM queue WHERE ID = ?', (row_id,))
