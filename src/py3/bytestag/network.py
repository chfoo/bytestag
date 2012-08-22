'''Networking'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from bytestag.events import (EventReactorMixin, EventReactor, EventScheduler,
    Task, EventID)
from bytestag.keys import bytes_to_b64
from socketserver import BaseRequestHandler
from threading import Thread
import base64
import binascii
import collections
import concurrent.futures
import io
import json
import logging
import os
import queue
import socket
import socketserver
import tempfile
import threading
import time
import zlib

__docformat__ = 'restructuredtext en'
_logger = logging.getLogger(__name__)


class UDP_INBOUND_EVENT(object):
    '''A UDP inbound event id'''
    pass


class UDPRequestHandler(BaseRequestHandler):
    '''UDP request handler for the UDP server'''

    def handle(self):
        _logger.debug('Handler')
        self.server.event_reactor.put(UDP_INBOUND_EVENT, self.client_address,
            self.request[0])


class DataPacket(collections.namedtuple('DataPacket', ['address', 'dict_obj',
'sequence_id'])):
    '''A JSON data packet.

    :var address: a tuple of (host, port_number)
    :var dict_obj: a :obj:`dict` containing the payload
    :var sequence_id: the sequence id
    '''

    __slots__ = ()


class IncomingTransfer(collections.namedtuple('IncomingTransfer',
['last_modified', 'timeout', 'read_transfer_task'])):
    '''A incoming transfer table entry'''

    __slots__ = ()


class UDPServer(EventReactorMixin, Thread, socketserver.UDPServer):
    '''UDP server'''

    def __init__(self, event_reactor, address=('127.0.0.1', 0)):
        EventReactorMixin.__init__(self, event_reactor)
        Thread.__init__(self)
        self.name = 'network-udp-server'
        self.daemon = True
        socketserver.UDPServer.__init__(self, address, UDPRequestHandler)
        self.event_reactor.register_handler(EventReactor.STOP_ID,
            self._stop_cb)

    def run(self):
        '''Start the server'''

        _logger.debug('Network udp server started')
        self.serve_forever()

    def _stop_cb(self, event_id):
        Thread(target=self.shutdown).start()
        _logger.debug('Network udp server stopped')


class UDPClient(object):
    '''UDP Client'''

    def __init__(self, socket_obj=None):
        self.socket = socket_obj or socket.socket(socket.AF_INET,
            socket.SOCK_DGRAM)

    def send(self, address, data):
        '''Send ``bytes`` to ``address``'''

        self.socket.sendto(data, address)


class JSONKeys(object):
    '''The keys used in the JSON data'''

    PAYLOAD = 'payload'
    SEQUENCE_ID = 'seq_id'
    REPLY_SEQUENCE_ID = 'reply_id'
    TRANSFER_ID = 'xfer_id'
    TRANSFER_DATA = 'xfer_data'


class ReplyTable(object):
    '''Manages the matching of sequence IDs to prevent forged UDP replies'''

    def __init__(self):
        self.out_table = {}
        self.in_table = {}

    def add_out_entry(self, sequence_id, address, event):
        '''Add an entry that expects a reply

        :Parameters:
            sequence_id
                The id of the packet send out
            address
                The destination of the packet
            event: :class:`threading.Event`
                The :class:`threading.Event` instance to wait on
        '''

        self.out_table[(sequence_id, address)] = event

    def get_out_entry(self, sequence_id, address):
        '''Get the Event instance

        :rtype: :class:`threading.Event`, ``None``
        '''

        return self.out_table.get((sequence_id, address))

    def remove_out_entry(self, sequence_id, address):
        '''Remove the entry'''

        del self.out_table[(sequence_id, address)]

    def add_in_entry(self, sequence_id, address, data_packet):
        '''Store the data packet reply to be retrieved be woken thread'''

        self.in_table[(sequence_id, address)] = data_packet

    def get_in_entry(self, sequence_id, address):
        '''Get the stored data packet

        :rtype: :class:`DataPacket`, ``None``
        '''

        return self.in_table.get((sequence_id, address))

    def remove_in_entry(self, sequence_id, address):
        '''Delete the stored data packet'''

        del self.in_table[(sequence_id, address)]


class Network(EventReactorMixin):
    '''Network controller

    :CVariables:
        MAX_UDP_PACKET_SIZE
            The maximum UDP packet size allowed
        DEFAULT_TIMEOUT
            The time in seconds before a reply is timed out
        STREAM_DATA_SIZE
            The size in bytes of the parts of the file transmitted
    '''

    MAX_UDP_PACKET_SIZE = 65507  # bytes
    DEFAULT_TIMEOUT = 10  # seconds
    STREAM_DATA_SIZE = 1024  # bytes
    SEQUENCE_ID_SIZE = 20  # bytes
    DEFAULT_POOL_SIZE = 20

    def __init__(self, event_reactor, address=('127.0.0.1', 0)):
        EventReactorMixin.__init__(self, event_reactor)
        self._server = UDPServer(event_reactor, address=address)
        # By passing in the same socket object to the client, this method
        # allows other nodes to reply to our server's port.
        self._client = UDPClient(socket_obj=self._server.socket)
        self._reply_table = ReplyTable()
        self._incoming_transfers = {}
        self._pool_executor = concurrent.futures.ThreadPoolExecutor(
            Network.DEFAULT_POOL_SIZE)
        self._event_scheduler = EventScheduler(event_reactor)
        self._transfer_timer_id = EventID(self, 'Clean transfers')

        self._register_handlers()
        self._server.start()

    @property
    def server_address(self):
        '''The address of the server'''

        return self._server.server_address

    def _register_handlers(self):
        '''Register the event callbacks'''

        self.event_reactor.register_handler(UDP_INBOUND_EVENT,
            self._udp_incoming_callback)
        self.event_reactor.register_handler(EventReactor.STOP_ID,
            self._stop_callback)
        self.event_reactor.register_handler(self._transfer_timer_id,
            self._clean_transfer)

    def _stop_callback(self, event_id):
        pass

    def _clean_transfer(self, event_id, transfer_id):
        '''Remove timed out file transfer'''

        last_modified, timeout, task = self._incoming_transfers[transfer_id]

        if last_modified + timeout < time.time():
            _logger.debug('Cleaned out transfer %s', transfer_id)
            del self._incoming_transfers[transfer_id]
            task.transfer(None)
        else:
            _logger.debug('Still alive transfer %s', transfer_id)
            self._event_scheduler.add_one_shot(timeout,
                self._transfer_timer_id, transfer_id)

    def _udp_incoming_callback(self, event_id, address, data):
        '''udp incoming'''

        _logger.debug('UDP %s←%s %s', self.server_address, address,
            data[:160])
        packet_dict = self._unpack_udp_data(data)

        if not packet_dict:
            return

        data_packet = DataPacket(address, packet_dict,
            packet_dict.get(JSONKeys.SEQUENCE_ID) \
            or packet_dict.get(JSONKeys.REPLY_SEQUENCE_ID))

        if JSONKeys.REPLY_SEQUENCE_ID in packet_dict:
            self._accept_reply(data_packet)
        elif JSONKeys.TRANSFER_ID in packet_dict:
            self._accept_transfer(data_packet)
        else:
            self._accept_packet(data_packet)

    def _accept_packet(self, data_packet):
        self.receive_callback(data_packet)

    def receive_callback(self, data_packet):
        '''The function called when a data packet arrives.

        :Parameters:
            data_packet: :class:`DataPacket`
                The incoming data packet

        This function is called for packets that are not replies. Implementors
        of this class should override this method.
        '''

        raise NotImplementedError()

    def expect_incoming_transfer(self, transfer_id, timeout=DEFAULT_TIMEOUT,
    read_transfer_task_class=None):
        '''Allow a transfer for download.

        :Parameters:
            transfer_id: ``str``
                A transfer id that the other client use for transferring data.
            timeout: ``int`` ``float``
                Time in seconds before the transfer times out.

        :rtype: :class:`ReadTransferTask`
        :return: A future that returns a file object that may have been
            interrupted. The progress is the number of bytes downloaded.
        '''

        read_transfer_task_class = read_transfer_task_class or ReadTransferTask
        read_transfer_task = read_transfer_task_class(('', 0))
        self._incoming_transfers[transfer_id] = IncomingTransfer(
            time.time(), timeout, read_transfer_task)

        self._event_scheduler.add_one_shot(timeout, self._transfer_timer_id,
            transfer_id)

        self._pool_executor.submit(read_transfer_task)

        return read_transfer_task

    def _accept_reply(self, data_packet):
        '''Process a reply and allow a future to resume'''

        sequence_id = data_packet.sequence_id
        address = data_packet.address

        event = self._reply_table.get_out_entry(sequence_id,
            address)

        if not event:
            _logger.debug('Unknown seq id %s, packet discarded', sequence_id)
            return

        self._reply_table.remove_out_entry(sequence_id, address)
        self._reply_table.add_in_entry(sequence_id, address, data_packet)
        event.set()

    def _accept_transfer(self, data_packet):
        '''Process a file transfer'''

        transfer_id = data_packet.dict_obj[JSONKeys.TRANSFER_ID]

        if transfer_id in self._incoming_transfers:
            if JSONKeys.TRANSFER_DATA in data_packet.dict_obj:
                self._read_transfer(data_packet, transfer_id)
                return

        _logger.debug('Transfer discarded')

    def _read_transfer(self, data_packet, transfer_id):
        '''Read data'''

        _logger.debug('Read transfer')

        read_transfer_task = self._incoming_transfers[transfer_id
            ].read_transfer_task
        data_str = data_packet.dict_obj[JSONKeys.TRANSFER_DATA]
        read_transfer_task.address = data_packet.address

        if data_str is None:
            read_transfer_task.transfer(None)
            _logger.debug('Read transfer finished')

            return
        else:
            try:
                data = base64.b64decode(data_str.encode())
            except binascii.Error as e:
                _logger.debug('Decode error %s', e)
                return

            read_transfer_task.transfer(data)
            _logger.debug('Read transfer len=%d', len(data))

        if read_transfer_task.is_running:
            d = {
                JSONKeys.TRANSFER_ID: transfer_id
            }

            self.send_answer_reply(data_packet, d)
        else:
            _logger.debug('Transfer aborted')

    def _pack_udp_data(self, packet_dict):
        '''Pack the dict into a format suitable for transmission.

        The format currently is JSON.
        '''

        data = zlib.compress(json.dumps(packet_dict).encode())

        if len(data) < Network.MAX_UDP_PACKET_SIZE:
            _logger.debug('Packed data %s', data[:20])
            return data
        else:
            raise Exception('data size too large')

    def _unpack_udp_data(self, data):
        '''Convert the data into a dict'''

        try:
            dict_obj = json.loads(zlib.decompress(data).decode())
        except Exception as e:
            _logger.debug('Failed json parsing %s', e)
            return

        if not isinstance(dict_obj, dict):
            _logger.debug('Not a dict')
            return

        return dict_obj

    def send(self, address, dict_obj, timeout=None):
        '''Send the ``dict`` to address

        :Parameters:
            address: ``tuple``
                A 2-tuple with the host and port number.
            dict_obj: ``dict``
                The ``dict`` that will be converted to JSON format.
            timeout: ``None``, ``int``, ``float``, ``True``
                If `timeout` is a number, the class will attempt to ensure
                delivery and wait for a reply. A future will be returned.
                If ``True``, the default timeout will be used.

        :rtype: ``None``, :class:`SendTask`
        :return: Returns a :class:`SendTask` if timeout is given.
            The result is either :class:`DataPacket` or ``None``.
        '''

        if timeout is None:
            self._send_plain(address, dict_obj)
        else:
            if timeout is True:
                timeout = Network.DEFAULT_TIMEOUT

            return self._send_expect_reply(address, dict_obj, timeout)

    def _send_plain(self, address, dict_obj):
        '''Send the data as a single UDP packet'''

        _logger.debug('Dict %s→%s', self.server_address, address)
        self._client.send(address, self._pack_udp_data(dict_obj))

    def _send_expect_reply(self, address, dict_obj, timeout=DEFAULT_TIMEOUT):
        '''Send the data and wait for a reply

        :rtype: :class:`SendTask`
        '''

        _logger.debug('Dict %s→%s timeout=%d', self.server_address,
            address, timeout)
        sequence_id = self.new_sequence_id()

        event = threading.Event()
        self._reply_table.add_out_entry(sequence_id, address, event)

        packet_dict = dict_obj.copy()
        packet_dict[JSONKeys.SEQUENCE_ID] = sequence_id

        def send_fn():
            self._client.send(address, self._pack_udp_data(packet_dict))

        send_task = SendTask(send_fn, sequence_id, address,
            self._reply_table, event, timeout)

        self._pool_executor.submit(send_task)

        return send_task

    def send_answer_reply(self, source_data_packet, dict_obj):
        '''Send ``dict`` that is a response to a incoming data packet

        :Parameters:
            source_data_packet: :class:`DataPacket`
                The original incoming data packet to respond to.
            dict_obj: ``dict``
                The data to send back

        Use this function to reply to packets that expect a response. This
        function automatically adds sequence IDs the reply packet.
        '''

        address = source_data_packet.address
        sequence_id = source_data_packet.sequence_id
        _logger.debug('Dict reply %s→%s seq_id=%s', self.server_address,
            address, sequence_id)

        packet_dict = dict_obj.copy()
        packet_dict[JSONKeys.REPLY_SEQUENCE_ID] = sequence_id

        self._client.send(address, self._pack_udp_data(packet_dict))

    def send_bytes(self, address, transfer_id, bytes_,
    timeout=DEFAULT_TIMEOUT):
        '''Transfer data to another client.

        :Parameters:
            address: ``tuple``
                A 2-tuple with host and port number.
            bytes_: ``bytes``
                The data to send.
            timeout: ``int``, ``float``
                The time in seconds before the transfer times out.
            transfer_id: ``str``, ``None``
                The transfer ID to be used. If ``None``, an ID will be
                created automatically.

        :see: :func:`send_file`
        :rtype: :class:`SendFileTask`
        '''

        f = io.BytesIO(bytes_)

        return self.send_file(address, transfer_id, f, timeout)

    def send_file(self, address, transfer_id, file_, timeout=DEFAULT_TIMEOUT):
        '''Transfer data to another client.

        :Parameters:
            address: ``tuple``
                A 2-tuple with host and port number.
            file_: ``str``, ``object``
                A filename or a file-like object which has ``read``.
            timeout: ``int``, ``float``
                The time in seconds before the transfer times out.
            transfer_id: ``str``, ``None``
                The transfer ID to be used. If ``None``, an ID will be
                created automatically.

        :rtype: :class:`SendFileTask`
        :return: A future that returns an ``int`` that is the number of bytes
            sent.
        '''

        if hasattr(file_, 'read'):
            source_file = file_
        else:
            source_file = open(file_, 'rb')

        transfer_id = transfer_id or self.new_sequence_id()

        _logger.debug('Send file %s→%s', self.server_address, address)

        send_file_task = SendFileTask(self, address, source_file,
            transfer_id, timeout)

        self._pool_executor.submit(send_file_task)

        return send_file_task

    def new_sequence_id(self):
        '''Generate a new sequence ID.

        :rtype: ``str``
        '''

        return bytes_to_b64(os.urandom(Network.SEQUENCE_ID_SIZE))


class ReadTransferTask(Task):
    '''Downloads data from a contact and returns a file object.'''

    def __init__(self, address):
        Task.__init__(self)
        self._file = tempfile.SpooledTemporaryFile(1048576)
        self._bytes_queue = queue.Queue(1)
        self.address = address

    def transfer(self, bytes_):
        self._bytes_queue.put(bytes_)

    def run(self):
        while self.is_running:
            try:
                bytes_ = self._bytes_queue.get(timeout=2)
            except queue.Empty:
                continue

            if bytes_:
                self.progress = len(bytes_)
                self._file.write(bytes_)
            else:
                break

        self._file.seek(0)
        return self._file


class SendFileTask(Task):
    '''Returns the number of bytes sent.'''
    def run(self, network, address, source_file, transfer_id, timeout):
        self.progress = 0

        while self.is_running:
            data = source_file.read(Network.STREAM_DATA_SIZE)

            d = {
                JSONKeys.TRANSFER_ID: transfer_id,
                JSONKeys.TRANSFER_DATA: bytes_to_b64(data),
            }

            if data:
                future = network.send(address, d, timeout)
                data_packet = future.result()

                if data_packet and data_packet.dict_obj.get(
                JSONKeys.TRANSFER_ID) == transfer_id:
                    self.progress += len(data)
            else:
                d[JSONKeys.TRANSFER_DATA] = None

                network.send(address, d)

                break

        return self.progress


class SendTask(Task):
    '''Send a data packet and return the response.

    The result returned is either `None` or :class:`DataPacket`.
    '''

    def run(self, send_fn, sequence_id, address, reply_table, event, timeout,
    num_attempts=2):
        for i in range(num_attempts):
            _logger.debug('SendTask →%s attempt=%d', address, i)
            send_fn()
            event.wait(timeout / num_attempts)

            data_packet = reply_table.get_in_entry(sequence_id, address)

            if data_packet:
                reply_table.remove_in_entry(sequence_id, address)
                _logger.debug('SendTask got confirm →%s attempt=%d', address,
                    i)
                return data_packet

        _logger.debug('SendTask no reply →%s attempt=%d', address, i)
        return data_packet
