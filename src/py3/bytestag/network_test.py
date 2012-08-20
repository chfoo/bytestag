from bytestag.events import EventReactor, EventScheduler
from bytestag.network import UDPServer, UDPClient, Network, ReplyTable
import bytestag.network
import hashlib
import io
import logging
import threading
import unittest

_logger = logging.getLogger(__name__)


class TestUDP(unittest.TestCase):
    def test_udp(self):
        '''It should be able to send itself a udp packet through events'''

        event_reactor = EventReactor()
        server = UDPServer(event_reactor)
        client = UDPClient()

        server.start()
        reactor_thread = threading.Thread(target=event_reactor.start)
        reactor_thread.daemon = True
        reactor_thread.start()

        data = None

        def my_callback(event_id, address, data_):
            nonlocal data

            data = data_  # @UnusedVariable

            event_reactor.put(EventReactor.STOP_ID)

        event_reactor.register_handler(
            bytestag.network.UDP_INBOUND_EVENT, my_callback)

        client.send(server.server_address, b'hello')

        reactor_thread.join(1)
        event_reactor.put(EventReactor.STOP_ID)

        self.assertEqual(data, b'hello')


class TestNetworkControllerComponents(unittest.TestCase):
    def test_udp_packing(self):
        '''It should pack and unpack the data symmetrically'''

        event_reactor = EventReactor()
        nc = Network(event_reactor)

        d = {'my_key': 123}

        self.assertEqual(d, nc._unpack_udp_data(nc._pack_udp_data(d)))

    def test_faulty_udp_unpacking_bad_json(self):
        '''It should return None if bad json parsing'''

        event_reactor = EventReactor()
        nc = Network(event_reactor)
        self.assertFalse(nc._unpack_udp_data(b'{"hello:}'))


class TestNetworkControllerMultiNode(unittest.TestCase):
    TIMEOUT = 5

    def setup_nodes(self, count=2):
        _logger.debug('Network setup---')

        self.er = []
        self.er_thread = []
        self.nc = []
        self.timer = []

        for i in range(count):
            self.er.append(EventReactor())
            er_thread = threading.Thread(target=self.er[i].start)
            er_thread.daemon = True
            er_thread.name = 'event-reactor-thread-%d' % i

            er_thread.start()
            self.er_thread.append(er_thread)
            self.nc.append(Network(self.er[i]))

            timer = EventScheduler(self.er[i])

            timer.add_one_shot(5, EventReactor.STOP_ID)
            self.timer.append(timer)
            _logger.debug('Server %d at %s', i, self.nc[i].server_address)

        self.stuff = {}

    def stop_event_reactors(self):
        for er in self.er:
            er.put(EventReactor.STOP_ID)

    def join_event_reactors(self):
        for er_thread in self.er_thread:
            er_thread.join()

    def test_incoming_send_packet(self):
        '''Server 0 should send a packet to server 1'''

        self.setup_nodes()

        def my_cb(data_packet):
            self.stuff = data_packet.dict_obj

            self.stop_event_reactors()

        self.nc[1].receive_callback = my_cb

        self.nc[0].send(self.nc[1].server_address, {'hello': True})

        self.join_event_reactors()

        self.assertEqual(self.stuff, {'hello': True})

    def test_expect_reply(self):
        '''It should send a packet and the other server replies'''

        self.setup_nodes()

        def other_server_cb(data_packet):
            self.stuff['1st_server_msg'] = data_packet.dict_obj

            self.nc[1].send_answer_reply(data_packet, {'kittehs': 3})

        self.nc[1].receive_callback = other_server_cb

        future = self.nc[0].send(self.nc[1].server_address, {'hello': True},
            timeout=self.TIMEOUT)
        data_packet = future.result(self.TIMEOUT)
        self.stuff['2nd_server_msg'] = data_packet.dict_obj

        self.stop_event_reactors()
        self.join_event_reactors()

        self.assertEqual(self.stuff['1st_server_msg']['hello'], True)
        self.assertEqual(self.stuff['2nd_server_msg']['kittehs'], 3)

    def test_expect_reply_failure(self):
        '''It should send a packet and it times-out'''

        self.setup_nodes()

        def other_server_cb(data_packet):
            # Simulate lost packet
            pass

        self.nc[1].receive_callback = other_server_cb

        future = self.nc[0].send(self.nc[1].server_address,
            {'hello': True}, timeout=0.0)

#        self.nc[0]._process_unreplied_cb(None)

        data_packet = future.result(self.TIMEOUT)
        self.stuff['2nd_server_msg'] = data_packet

        self.stop_event_reactors()

        self.join_event_reactors()

        self.assertEqual(self.stuff['2nd_server_msg'], None)

    def test_send_file(self):
        '''It should transfer a file'''

        transfer_id = '123'
        f = io.BytesIO()
        data = b'\x0F\xF0' * 10000
        hasher = hashlib.sha1(data)

        f.write(data)
        f.seek(0)

        self.setup_nodes(2)

        read_transfer_task = self.nc[1].expect_incoming_transfer(transfer_id,
            timeout=self.TIMEOUT)

        future = self.nc[0].send_file(self.nc[1].server_address, transfer_id,
            f, timeout=self.TIMEOUT)

        bytes_sent = future.result()
        f_other = read_transfer_task.result()

        self.stop_event_reactors()

        self.assertEqual(bytes_sent, len(data))

        self.join_event_reactors()

        f_other.seek(0)
        test_hasher = hashlib.sha1(f_other.read())

        self.assertEqual(len(data), f_other.tell())
        self.assertEqual(test_hasher.digest(), hasher.digest())


class TestReplyTable(unittest.TestCase):
    def test_add_remove_out(self):
        '''It should add and remove'''

        table = ReplyTable()

        table.add_out_entry(0, 0, None)
        self.assertEqual(table.get_out_entry(0, 0), None)
        table.remove_out_entry(0, 0)
        self.assertFalse(table.get_out_entry(0, 0))

    def test_add_remove_in(self):
        '''It should add and remove'''

        table = ReplyTable()

        table.add_in_entry(0, 0, None)
        self.assertEqual(table.get_in_entry(0, 0), None)
        table.remove_in_entry(0, 0)
        self.assertFalse(table.get_in_entry(0, 0))
