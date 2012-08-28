'''Key-value pair management'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from bytestag.events import Observer
from bytestag.keys import KeyBytes
import abc
import collections
import itertools
import logging

__docformat__ = 'restructuredtext en'
_logger = logging.getLogger(__name__)


class KVPID(collections.namedtuple('KVPID', ['key', 'index'])):
    '''The components of a key.

    :var key: a :class:`.KeyBytes`
    :var index: a :class:`.KeyBytes`
    '''

    __slots__ = ()

    def __str__(self):
        return '<KVPID {}:{}>'.format(self.key.base16, self.index.base16)


class KVPTable(metaclass=abc.ABCMeta):
    '''A base class for key-value tables.

    This table supports Python idioms for add and removing values::

       table[kvpid] = b'123'
       kvpid in table
       del table[kvpid]
    '''

    def __init__(self):
        self._value_changed_observer = Observer()

    @property
    def value_changed_observer(self):
        '''The observer for value changes.

        :rtype: :class:`.Observer`
        '''

        return self._value_changed_observer

    def __contains__(self, kvpid):
        assert isinstance(kvpid, KVPID)

        return self._contains(kvpid)

    def __getitem__(self, kvpid):
        assert isinstance(kvpid, KVPID)

        return self._getitem(kvpid)

    def __setitem__(self, kvpid, value):
        assert isinstance(kvpid, KVPID)
        assert isinstance(value, bytes)
        assert KeyBytes.validate_hash_value(kvpid.index, value)

        result = self._setitem(kvpid, value)

        self._value_changed_observer(kvpid)

        return result

    def __delitem__(self, kvpid):
        assert isinstance(kvpid, KVPID)

        self._delitem(kvpid)
        self._value_changed_observer(kvpid)

    @abc.abstractmethod
    def _contains(self, kvpid):
        pass

    @abc.abstractmethod
    def _getitem(self, kvpid):
        pass

    @abc.abstractmethod
    def _setitem(self, kvpid, value):
        pass

    @abc.abstractmethod
    def indices(self, key):
        '''Return the indicies associated with the key.

        :rtype: :obj:`list`
        :returns: a list of indices :class:`.KeyBytes`
        '''
        pass

    @abc.abstractmethod
    def _delitem(self, kvpid):
        pass

    @abc.abstractmethod
    def keys(self):
        '''Return an iterator of :class:`KVPID`'''
        pass

    @abc.abstractmethod
    def record(self, kvpid):
        '''Return the :class:`KVPRecord` associated with the :class:`KVPID`'''
        pass

    def records_by_key(self, key):
        '''Return a list of :class:`KVPRecord` associated with given key.'''

        l = []

        for index in self.indices(key):
            record = self.record(KVPID(key, index))
            assert record
            l.append(record)

        return l

    @abc.abstractmethod
    def is_acceptable(self, kvpid, size, timestamp):
        '''Return whether the table accepts adding new keys.

        :rtype: :obj:`bool`
        '''

        pass


class KVPRecord(metaclass=abc.ABCMeta):
    '''Information about a key-value pair'''

    @abc.abstractproperty
    def key(self):
        '''The key of the key-value pair.

        :rtype: :class:`.KeyBytes`
        '''
        pass

    @abc.abstractproperty
    def index(self):
        '''The index of the key-value pair.

        :rtype: :class:`.KeyBytes`
        '''
        pass

    @abc.abstractproperty
    def value(self):
        '''The value of the key-value pair.

        :rtype: :obj:`bytes`
        '''
        pass

    @abc.abstractproperty
    def size(self):
        '''The length of the value.

        :rtype: :obj:`int`
        '''
        pass

    @abc.abstractproperty
    def timestamp(self):
        '''The publication timestamp of the key-value pair.

        :rtype: :obj:`int`
        '''
        pass

    @timestamp.setter
    def timestamp(self, seconds):
        pass

    @abc.abstractproperty
    def time_to_live(self):
        '''The time in seconds the record is kept.

        :rtype: :obj:`int`
        '''
        pass

    @time_to_live.setter
    def time_to_live(self, seconds):
        pass

    @abc.abstractproperty
    def is_original(self):
        '''Whether this client is the original publisher of the key-value pair.

        :rtype: :obj:`bool`
        '''
        pass

    @is_original.setter
    def is_original(self, b):
        pass

    @abc.abstractproperty
    def last_update(self):
        '''The timestamp of when the value was published or replicated.

        :rtype: :obj:`int`
        '''
        pass

    @last_update.setter
    def last_update(self, seconds):
        pass


class AggregatedKVPTable(KVPTable):
    '''Combines several :class:`KVPTable`'''

    def __init__(self, primary_table, tables):
        '''
        :param primary_table: The table where values are set.
        :param tables: A list of tables which are generally read-only.
        '''

        KVPTable.__init__(self)
        self._tables = tuple(tables)
        self._primary_table = primary_table

        for table in tables:
            table.value_changed_observer.register(self.value_changed_observer)

    @property
    def tables(self):
        return self._tables

    @property
    def primary_table(self):
        return self._primary_table

#    @primary_table.setter
#    def primary_table(self, table):
#        self._primary_table = table

    def _contains(self, kvpid):
        for table in self._tables:
            if kvpid in table:
                return True

        return False

    def _getitem(self, kvpid):
        for table in self._tables:
            if kvpid in table:
                return table[kvpid]

        raise IndexError()

    def _setitem(self, kvpid, value):
        self._primary_table[kvpid] = value

    def indices(self, key):
        l = []

        for table in self._tables:
            l.extend(table.indices(key))

        return l

    def _delitem(self, kvpid):
        del self._primary_table[kvpid]

    def keys(self):
        return itertools.chain(*[table.keys() for table in self._tables])

    def record(self, kvpid):
        for table in self._tables:
            if kvpid in table:
                return table.record(kvpid)

        raise IndexError()

    def records_by_key(self, key):
        l = []

        for table in self._tables:
            for index in table.indices(key):
                _logger.debug('asdfsfasdf %s:%s', key, index)
                record = self.record(KVPID(key, index))
                assert record
                l.append(record)

        return l

    def is_acceptable(self, kvpid, size, timestamp):
        if kvpid not in self:
            return self._primary_table.is_acceptable(kvpid, size, timestamp)
