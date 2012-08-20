from bytestag.events import EventReactor, Observer, EventID, asynchronous
import threading
import unittest


class TestEventReactor(unittest.TestCase):
    def test_reactor(self):
        '''It should process 1 event and then stop'''

        my_id = EventID('my_id')
        self.test_value = False

        def my_callback(event_id):
            self.assertEqual(my_id, event_id)
            self.test_value = True

        event_reactor = EventReactor()
        event_reactor.register_handler(my_id, my_callback)
        event_reactor.put(my_id)
        event_reactor.put(EventReactor.STOP_ID)
        event_reactor.start()
        self.assertTrue(self.test_value)


class TestObserver(unittest.TestCase):
    # TODO: test one shot
    def test_observer(self):
        '''It should activate the callback functions'''

        observer = Observer()

        def f1(s):
            self.f1 = s

        def f2(s):
            self.f2 = s

        observer.register(f1)
        observer.register(f2)
        observer('kitteh')

        self.assertEqual('kitteh', self.f1)
        self.assertEqual('kitteh', self.f2)


class TestAsync(unittest.TestCase):
    def test_async(self):
        v = None

        @asynchronous()
        def f():
            nonlocal v

            v = True  # @UnusedVariable

        thread = f()

        self.assertIsInstance(thread, threading.Thread)

        thread.join()

        self.assertEqual(v, True)

    @unittest.skip('Causes exception printout on Nose unit test')
    def test_async_error(self):
        v = None

        @asynchronous()
        def f():
            nonlocal v

            v = True  # @UnusedVariable

            raise Exception('my intentional exception')

        thread = f()

        self.assertIsInstance(thread, threading.Thread)

        thread.join()

        self.assertEqual(v, True)
