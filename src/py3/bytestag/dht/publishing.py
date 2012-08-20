'''DHT publisher

This module includes classes that scan tables for values to publish
or replicate.
'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from bytestag.dht.network import DHTNetwork
from bytestag.events import (EventReactorMixin, EventScheduler, EventID,
    asynchronous)
from bytestag.queue import BigDiskQueue
import logging
import threading
import time

__docformat__ = 'restructuredtext en'
_logger = logging.getLogger(__name__)


class Replicator(EventReactorMixin):
    '''Replicates values typically stored into the cache by other nodes.'''

    def __init__(self, event_reactor, dht_network, kvp_table, fn_task_slot):
        '''
        :type event_reactor: :class:`.EventReactor
        :type dht_network: :class:`.DHTNetwork`
        :type kvp_table: :class:`.KVPTable`
        :param fn_task_slot: A slot that represents uploads.
        :type fn_task_slot: :class:`FnTaskSlot`
        '''

        EventReactorMixin.__init__(self, event_reactor)
        self._dht_network = dht_network
        self._kvp_table = kvp_table
        self._event_scheduler = EventScheduler(event_reactor)
        self._timer_id = EventID(self, 'Replicate')
        self._thread_event = threading.Event()
        self._fn_task_slot = fn_task_slot

        self._event_reactor.register_handler(self._timer_id, self._timer_cb)
        self._event_scheduler.add_periodic(DHTNetwork.TIME_REPLICATE,
            self._timer_id)
        self._loop()

    def _timer_cb(self, event_id):
        self._thread_event.set()

    @asynchronous(name='Replicate Values')
    def _loop(self):
        while True:
            self._thread_event.wait()
            _logger.debug('Replicating values')
            self._thread_event.clear()

            for kvpid in self._kvp_table.keys():
                kvp_record = self._kvp_table.record(kvpid)

                if kvp_record.is_original:
                    continue

                if kvp_record.timestamp + kvp_record.time_to_live \
                < time.time():
                    continue

                _logger.debug('Replicating value %s', kvpid)
                self._fn_task_slot.add(self._dht_network.store_value,
                    kvpid.key, kvpid.index)

            _logger.debug('Value replication finished')

            self._clean_table()

    def _clean_table(self):
        if hasattr(self._kvp_table, 'clean'):
            self._kvp_table.clean()
        elif hasattr(self._kvp_table, 'tables'):
            for table in self._kvp_table.tables:
                if hasattr(table, 'clean'):
                    table.clean()


class Publisher(EventReactorMixin):
    '''Publishes values typically created by the client.'''

    REPUBLISH_CHECK_INTERVAL = 3600

    def __init__(self, event_reactor, dht_network, kvp_table, fn_task_slot):
        '''
        :type event_reactor: :class:`.EventReactor
        :type dht_network: :class:`.DHTNetwork`
        :type kvp_table: :class:`.KVPTable`
        :param fn_task_slot: A slot that represents uploads.
        :type fn_task_slot: :class:`FnTaskSlot`
        '''

        EventReactorMixin.__init__(self, event_reactor)
        self._dht_network = dht_network
        self._kvp_table = kvp_table
        self._event_scheduler = EventScheduler(event_reactor)
        self._timer_id = EventID(self, 'Publish timer')
        self._schedule_id = EventID(self, 'Publish schedule')
        self._scheduled_kvpids = set()
        self._schedule_lock = threading.Lock()
        self._scan_event = threading.Event()
        self._publish_queue = BigDiskQueue()
        self._fn_task_slot = fn_task_slot

        self._event_reactor.register_handler(self._schedule_id,
            self._publish_cb)
        self._event_reactor.register_handler(self._timer_id, self._timer_cb)
        self._kvp_table.value_changed_observer.register(self._table_change_cb)

        self._event_scheduler.add_periodic(Publisher.REPUBLISH_CHECK_INTERVAL,
            self._timer_cb)

        self._scan_loop()
        self._publish_loop()

    @asynchronous(name='Publish loop')
    def _publish_loop(self):
        while True:
            kvpid = self._publish_queue.get()

            _logger.debug('Publishing %s', kvpid)

            self._fn_task_slot.add(self._dht_network.store_value, kvpid.key,
                kvpid.index)

    def _schedule_for_publish(self, abs_time, kvpid):
        with self._schedule_lock:
            if kvpid in self._scheduled_kvpids:
                return

            self._scheduled_kvpids.add(kvpid)

        self._event_scheduler.add_absolute(abs_time, self._schedule_id, kvpid)

    def _publish_cb(self, event_id, kvpid):
        self._publish_queue.put(kvpid)

    def _table_change_cb(self, *args):
        self._scan_event.set()

    def _timer_cb(self, event_id):
        self._scan_event.set()

    @asynchronous(name='Publish scan loop')
    def _scan_loop(self):
        while True:
            self._scan_event.wait()
            _logger.debug('Scanning database for publishing')
            self._scan_event.clear()

            current_time = time.time()

            for kvpid in self._kvp_table.keys():
                kvp_record = self._kvp_table.record(kvpid)

                if not kvp_record.is_original:
                    continue

                if kvp_record.last_update == 0:
                    republish_time = current_time
                else:
                    republish_time = \
                        kvp_record.last_update + DHTNetwork.TIME_REPUBLISH

                next_interval = Publisher.REPUBLISH_CHECK_INTERVAL

                if republish_time - next_interval < current_time:
                    self._schedule_for_publish(republish_time, kvpid)
