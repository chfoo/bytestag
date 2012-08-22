'''Node tables'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from bytestag.keys import KeyBytes, compute_bucket_number
import io
import logging
import random
import threading
import time

__docformat__ = 'restructuredtext en'
_logger = logging.getLogger(__name__)


class Node(object):
    '''An end-point connection.

    This class implements equality and comparison operators using
    the key and address of the node.
    '''

    def __init__(self, key, address):
        '''Init

        :Parameters:
            key: :class:`.KeyBytes`
                The key of the node
            address
                The address of the node. The address is a tuple (host, port).
        '''

        self._key = key
        self._address = address

    @property
    def key(self):
        '''Return the key of the node

        :rtype: :class:`.KeyBytes`
        '''

        return self._key

    @property
    def address(self):
        '''Return the address of the node

        :rtype: ``tuple``
        '''

        return self._address

    def __str__(self):
        return '<Node %s %s>' % (self._key, self.address)

    def __eq__(self, other):
        return self._key == other.key \
            and self._address == other.address

    def __ne__(self, other):
        return not (self._key == other.key \
            and self._address == other.address)

    def __hash__(self):
        return hash(self._key) ^ hash(self._address)


class BucketFullError(Exception):
    '''Bucket is full

    :IVariables:
        bucket_number: ``int``
            The bucket number
        bucket: `Bucket`
            The `Bucket`
        node: `Node`
            The `Node`
    '''

    def __init__(self, *args, bucket_number=None, node=None, bucket=None):
        Exception.__init__(self, *args)
        self.bucket_number = bucket_number
        self.bucket = bucket
        self.node = node


class Bucket(object):
    '''A bucket of nodes.

    This class supports container methods with :class:`Node`.
    '''

    MAX_BUCKET_SIZE = 20  # constant k

    def __init__(self, number):
        self._number = number
        self._lock = threading.Lock()
        self._nodes = []
        self._last_update = 0
        self._full = False
        self._new_node = None

    @property
    def number(self):
        '''The bucket number

        :rtype: ``int``
        '''

        return self._number

    @property
    def nodes(self):
        '''The nodes in the bucket

        :rtype: ``list``
        :return: A ``list`` of `Node`
        '''

        return self._nodes

    @property
    def last_update(self):
        '''Return the time the bucket was last updated'''

        return self._last_update

    def __contains__(self, node):
        return node in self._nodes

    def __iter__(self):
        for node in self._nodes:
            yield node

    def __str__(self):
        sio = io.StringIO()
        sio.write('<Bucket {}\n'.format(self._number))

        for node in self._nodes:
            sio.write('  {}\n'.format(str(node)))

        sio.write('>')

        return sio.getvalue()

    def __len__(self):
        return len(self._nodes)

    def node_update(self, node):
        '''Add or move the node to end of list

        Once the bucket is full, the bucket is locked and any other nodes
        are ignored. To unlock the bucket, call either `keep_old_node` or
        `keep_new_node`.

        :raise BucketFullError: bucket is full
        '''

        _logger.debug('Bucket %s node update %s', self, node)

        with self._lock:
            if self._full:
                # The paper doesn't say what happens now, so we are ignoring
                # new nodes
                _logger.debug('Bucket %s full, ignored node update %s, ',
                    self, node)
                return

            if len(self._nodes) < Bucket.MAX_BUCKET_SIZE:
                if node in self._nodes:
                    self._nodes.remove(node)

                self._nodes.append(node)
                self._last_update = time.time()
            else:
                self._full = True
                self._new_node = node

                raise BucketFullError(node=self._nodes[0], bucket=self)

    def keep_old_node(self):
        '''Keep the old node

        The old node has responded
        '''

        assert self._full

        with self._lock:
            self._full = False
            self._last_update = time.time()

    def keep_new_node(self):
        '''Keep the new node

        The old node has *not* responded
        '''

        assert self._full

        with self._lock:
            self._full = False

            self._nodes.pop(0)
            self._nodes.append(self._new_node)
            self._last_update = time.time()


class RoutingTable(object):
    '''A list of buckets'''

    def __init__(self, key=None):
        self._buckets = tuple(Bucket(i) for i in range(KeyBytes.BIT_SIZE))
        self._key = key or KeyBytes()

    @property
    def buckets(self):
        '''The buckets'''
        return self._buckets

    @property
    def num_contacts(self):
        '''Return number of contacts'''

        return sum([len(bucket) for bucket in self._buckets])

    def __contains__(self, contact):
        bucket = self.get_bucket(contact)

        if bucket:
            return contact in bucket

    def __str__(self):
        sio = io.StringIO()
        sio.write('<Routing table\n')

        for bucket_number in range(len(self._buckets)):
            bucket = self._buckets[bucket_number]

            if bucket:
                sio.write(str(bucket))

        sio.write('>')

        return sio.getvalue()

    def __iter__(self):
        for bucket in self._buckets:
            for node in bucket:
                yield node

    def __getitem__(self, key):
        return self._buckets[key]

    def get_bucket(self, node):
        '''Get the appropriate bucket for the node

        :rtype: `Bucket`
        '''

        bucket_number = self.get_bucket_number(node)

        if bucket_number < KeyBytes.BIT_SIZE:
            return self._buckets[bucket_number]

    def get_bucket_number(self, node):
        '''Get the appropriate bucket number for the node

        :rtype: `int`
        '''

        return compute_bucket_number(self._key, node.key)

    def node_update(self, node):
        '''Call the appropriate bucket update'''

        if node.key == self._key:
            raise ValueError('Cannot add node that has our node id')

        bucket = self.get_bucket(node)

        bucket.node_update(node)

    def get_close_nodes(self, key, count=3):
        '''Return the closest nodes to a key

        :Parameters:
            key : :class:`.KeyBytes`
                The target key
            count: `int`
                The maximum length of the list returned

        :return: A ``list`` of `Node`
        :rtype: ``list``
        '''

        bucket_number = compute_bucket_number(self._key, key)
        bucket = self._buckets[bucket_number]

        if len(bucket) >= count:
            return random.sample(bucket.nodes, count)

        # Pick nodes from random buckets
        nodes = set(bucket.nodes)
        buckets = list(self._buckets)

        random.shuffle(buckets)

        for bucket in buckets:
            num_needed = min(len(bucket), count - len(nodes))

            for contact in random.sample(bucket.nodes, num_needed):
                nodes.add(contact)

            if len(nodes) == count:
                break

            assert len(nodes) <= count

        _logger.debug('Got %s close nodes', len(nodes))

        return list(nodes)

    def count_close(self, key):
        '''Return the number of node closer than the given key'''

        bucket = self._buckets[compute_bucket_number(self._key, key)]
        count = 0

        for node in bucket:
            if node.key.distance_int(key) < self._key.distance_int(key):
                count += 1

        return count
