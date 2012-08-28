'''Event handling'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from concurrent.futures.thread import ThreadPoolExecutor
from queue import Queue
from threading import Lock
from weakref import WeakValueDictionary
import functools
import heapq
import inspect
import itertools
import logging
import queue
import threading
import time

__docformat__ = 'restructuredtext en'
_logger = logging.getLogger(__name__)


class EventID(object):
    '''An event ID.

    This class' comparison equality depends on the arguments given.
    '''

    def __init__(self, arg, *args):
        self._args = tuple(itertools.chain((arg,), args))

        for arg in self._args:
            hash(arg)

    @property
    def args(self):
        return self._args

    def __str__(self):
        return '<EventID {}>'.format(self._args)

    def __hash__(self):
        if len(self._args) == 1:
            return hash(self._args[0])

        return functools.reduce(lambda x, y: hash(x) ^ hash(y), self._args)

    def __eq__(self, other):
        return self._args == other

    def __ne__(self, other):
        return self._args != other


class EventReactor(object):
    '''A reactor that demultiplexs events from other threads'''

    class STOP_ID(object):
        '''The identifier that stops all event reactors'''
        pass

    def __init__(self, max_queue_size=100):
        self._queue = Queue(max_queue_size)
        self._callback_table = {}
        self._callback_table_lock = Lock()
        self._max_queue_size = max_queue_size

    @property
    def queue_size(self):
        '''The current size of the queue.'''
        return self._queue.qsize()

    @property
    def max_queue_size(self):
        '''The maximum size of the queue.'''
        return self._max_queue_size

    def put(self, event_id, *event_data):
        '''Add an event to be dispatched

        :Parameters:
            event_id
                Any value that can be used as an index
            event_data
                Data to be passed to the callback function
        '''

        cur_queue_size = self._queue.qsize()

        _logger.debug('Event put %s queue_size=%d', event_id, cur_queue_size)

        if cur_queue_size > self._max_queue_size * 0.90:
            _logger.warning('Event queue is approaching limits: '
                'current=%d, max=%d', cur_queue_size, self._max_queue_size)

        try:
            self._queue.put((event_id, event_data), block=False)
        except queue.Full as e:
            _logger.exception('Event queue full')
            raise e

    def register_handler(self, event_id, handler_callback):
        '''Add a callback function to handle events

        :Parameters:
            event_id
                Any value that can be used as an index
            handler_callback
                A callable object such as a function or an instance with
                the ``__call__`` member
        '''

        with self._callback_table_lock:
            if event_id not in self._callback_table:
                self._callback_table[event_id] = []

            self._callback_table[event_id].append(handler_callback)
            _logger.debug('Registered handler %s=%s', event_id,
                handler_callback)

    def start(self):
        '''Start the event reactor'''

        self._run()

    def _run(self):
        '''Run the main loop'''

        _logger.debug('Event reactor started')

        while True:
            event_id, event_data = self._queue.get()
            if event_id in self._callback_table:
                for handler_callback in self._callback_table[event_id]:
                    try:
                        _logger.debug('Call handler=%s event_id=%s',
                            handler_callback, event_id)
                        handler_callback(event_id, *event_data)
                        _logger.debug('Call finished handler=%s event_id=%s',
                            handler_callback, event_id)
                    except Exception as e:
                        try:
                            _logger.exception(
                                'Handler exception at callback %s',
                                inspect.getsourcelines(handler_callback))
                        except IOError:
                            pass
                        raise e

            if event_id == EventReactor.STOP_ID:
                break

        _logger.debug('Event reactor finished')


class EventReactorMixin(object):
    '''A mix in to provide an ``event_reactor`` property'''

    def __init__(self, event_reactor):
        self._event_reactor = event_reactor

    @property
    def event_reactor(self):
        '''Return the event reactor

        :rtype: :class:`EventReactor`
        '''

        return self._event_reactor


@functools.total_ordering
class EventSchedulerEntry(object):
    '''An event scheduler entry.'''

    def __init__(self, abs_time, event_id, *event_data,
    periodic_interval=None):
        self.abs_time = abs_time
        self.event_id = event_id
        self.event_data = event_data
        self.periodic_interval = periodic_interval

    def __str__(self):
        return '<EventSchedulerEntry t={} event={} perodic={}>'.format(
            self.abs_time, self.event_id, self.periodic_interval)

    def __lt__(self, other):
        return self.abs_time < other.abs_time

    def __eq__(self, other):
        return self.abs_time == other.abs_time


class EventScheduler(threading.Thread, EventReactorMixin):
    '''Schedules events to be added to event reactors'''

    def __init__(self, event_reactor):
        threading.Thread.__init__(self)
        EventReactorMixin.__init__(self, event_reactor)
        self.name = 'Scheduler'
        self.daemon = True
        self._lock = threading.Lock()
        self._heap = []
        self._event = threading.Event()
        self._reschedule_id = EventID(self, 'EventReschedule')

        self.event_reactor.register_handler(self._reschedule_id,
            self._resched_callback)
        self.start()

    def _resched_callback(self, event_id, seconds, target_event_id,
    event_data):
        self.add_periodic(seconds, target_event_id, *event_data)

    def add_absolute(self, time, event_id, *event_data):
        '''Add an event to be scheduled at given time

        :Parameters:
            time: ``int``, ``float``
                The timestamp in the future
            event_id
                The indexable value to be used as an event ID
            event_data
                Any extra data to be passed
        '''

        _logger.debug('Add absolute %s %s', time, event_id)

        with self._lock:
            entry = EventSchedulerEntry(time, event_id, *event_data)
            heapq.heappush(self._heap, entry)

        self._event.set()

    def add_periodic(self, seconds, event_id, *event_data):
        '''Add an event to be scheduled periodically.

        :Parameters:
            seconds: ``int``, ``float``
                The interval in seconds
            event_id
                The indexable value to be used as an event ID
            event_data
                Any extra data to be passed
        '''

        _logger.debug('Add periodic %s %s', seconds, event_id)

        with self._lock:
            entry = EventSchedulerEntry(time.time() + seconds,
                event_id, *event_data, periodic_interval=seconds)
            heapq.heappush(self._heap, entry)

        self._event.set()

    def add_one_shot(self, seconds, event_id, *event_data):
        '''Add an event to be scheduled once.

        :Parameters:
            seconds: ``int``, ``float``
                The interval in seconds
            event_id
                The indexable value to be used as an event ID
            event_data
                Any extra data to be passed
        '''

        _logger.debug('Add one shot %s %s', seconds, event_id)

        with self._lock:
            entry = EventSchedulerEntry(time.time() + seconds,
                event_id, *event_data)
            heapq.heappush(self._heap, entry)

        self._event.set()

    def run(self):
        wait_time = None
        wait_time_skew = 0.1

        while True:
            _logger.debug('Sched wait')
            self._event.wait(timeout=wait_time)
            self._event.clear()
            _logger.debug('Sched run')

            entry = None

            with self._lock:
                if self._heap and self._heap[0].abs_time <= time.time():
                    entry = heapq.heappop(self._heap)

                if self._heap:
                    wait_time = self._heap[0].abs_time - time.time()
                    wait_time += wait_time_skew
                else:
                    wait_time = None

            if entry:
#                if self._attempt_put(entry):
#                    wait_time = 1
                self.event_reactor.put(entry.event_id, *entry.event_data)

                if entry.periodic_interval:
                    self.event_reactor.put(self._reschedule_id,
                        entry.periodic_interval, entry.event_id,
                        entry.event_data)

            _logger.debug('Sched fin')


class Observer(object):
    '''A callback manager.

    Example usage::

        >>> def my_function(some_arg):
        ...     print(some_arg)
        >>> observer = Observer()
        >>> observer.register(my_function)
        >>> observer('Observer activated!')
        'Observer activated!'

    '''

    def __init__(self, callback_fn=None, one_shot=False):
        '''
        :param callback_fn: An optional callback function.
        :param one_shot: If `True`, after the first activation, subsequent
            registers will automatically be called. Otherwise, the observer can
            activate unlimited times.
        '''

        self._one_shot = one_shot
        self._fired = False
        self._one_shot_args = None

        if callback_fn:
            self._fns = [callback_fn]
        else:
            self._fns = []

    def __call__(self, *args, **kwargs):
        '''Execute all registered callback functions'''

        self._fired = True

        if self._one_shot:
            self._one_shot_args = (args, kwargs)

        for fn in self._fns:
            fn(*args, **kwargs)

    def register(self, callback_fn):
        '''Register a callback function'''

        self._fns.append(callback_fn)

        if self._one_shot and self._fired:
            callback_fn(*self._one_shot_args[0], **self._one_shot_args[1])


class Task(object):
    '''An enhanced future.

    Pass an instance of this task to :class:`concurrent.futures.Executor`.
    Instead of using the future provided by the executor, use this instance.
    '''

    def __init__(self, *args, **kwargs):
        self._progress = None
        self._result = None
        self._observer = Observer(one_shot=True)
        self._is_running = False
        self._is_finished = False
        self._event = threading.Event()
        self._result = None
        self._hooked_tasks = []
        self._parent_tasks = []
        self._args = args
        self._kwargs = kwargs

    @property
    def progress(self):
        '''Return the progress made so far'''

        return self._progress

    @progress.setter
    def progress(self, o):
        self._progress = o

        for parent_task in self._parent_tasks:
            parent_task.progress = o

    @property
    def is_running(self):
        '''Return whether the task is running

        :rtype: ``bool``
        '''

        return self._is_running

    @property
    def is_finished(self):
        return self._is_finished

    @property
    def observer(self):
        '''Return the observer

        The observer will callback when the task is finished.

        :rtype: `Observer`
        '''

        return self._observer

    @property
    def result_(self):
        '''Return the result.

        Result may be ``None`` if the task is not finished.

        :see: :func:`result`
        '''

        return self._result

    @result_.setter
    def result_(self, o):
        self._result = o

    def hook_task(self, task):
        '''Hook another task into this task.

        This function should be called within the task so that `stop` will
        be propagated to the given task. Once the task finishes, it is
        automatically unhooked. As well, the task will update the progress.
        '''

        self._hooked_tasks.append(task)
        task._hooked(self)

    def _hooked(self, parent_task):
        '''A task has hooked us'''

        self._parent_tasks.append(parent_task)

        def unhook(*args):
            self._parent_tasks.remove(parent_task)
            parent_task._unhook_task(self)

        self.observer.register(unhook)

    def _unhook_task(self, task):
        '''Unhook a task'''

        self._hooked_tasks.remove(task)

    def stop(self):
        '''Request the task to stop'''

        self._is_running = False

        for task in self._hooked_tasks:
            task.stop()

    def _run_all(self):
        self._is_running = True

        try:
            self._result = self.run(*self._args, **self._kwargs)
        except Exception as e:
            _logger.exception('Error during task')
            raise e
        finally:
            self._is_finished = True
            self._event.set()
            self._observer(self._result)
            self._is_running = False

            return self._result

    def result(self, timeout=None):
        '''Wait and return the result'''

        self._event.wait(timeout)

        return self._result

    def run(self, *args, **kwargs):
        '''The task's main body.

        Implementors should override this function. This function
        should periodically check `is_running` and update `progress`.
        The function should return a value which is the result.
        '''

        raise NotImplementedError()

    def __call__(self):
        return self._run_all()


class FnTaskSlot(threading.Thread):
    '''Limit task execution'''

    def __init__(self, max_size=3):
        threading.Thread.__init__(self)
        self.daemon = True
        self.name = FnTaskSlot.__name__
        self._queue = queue.Queue(max_size)
        self._current_tasks = set()
        self._running = False
        self._max_size = max_size
        self._observer = Observer()

        self.start()

    def add(self, fn, *args, **kwargs):
        '''Executes function with given arguments.

        This function blocks until the slot is not full.

        :rtype: :class:`Task`
        :returns: The Task that given ``fn`` returns.
        '''

        event = threading.Event()
        self._queue.put((event, fn, args, kwargs))
        event.wait()

        return event.task

    def add_no_block(self, fn, *args, **kwargs):
        self._queue.put_nowait((fn, args, kwargs))

    @property
    def queue(self):
        return self._queue

    @property
    def current_tasks(self):
        return self._current_tasks

    @property
    def observer(self):
        '''An observer that fires when a task is added or removed.

        The observer callback arguments are:

        1. :obj:`bool` - If `True`, then the task is added. Otherwise,
           the task was removed.
        2. :class:`Task` - The task added or removed.
        '''

        return self._observer

    def run(self):
        self._running = True

        while self._running:
            if len(self._current_tasks) < self._max_size:

                if self._current_tasks:
                    timeout = 1
                else:
                    timeout = None

                try:
                    event, fn, args, kwargs = self._queue.get(timeout=timeout)
                except queue.Empty:
                    pass
                else:
                    _logger.debug('Fn task slot execute')
                    task = fn(*args, **kwargs)
                    event.task = task
                    event.set()

                    self._current_tasks.add(task)
                    self._observer(True, task)

            for task in frozenset(self._current_tasks):
                task.result(timeout=1)

                if task.is_finished:
                    self._current_tasks.remove(task)
                    self._observer(False, task)

    def stop(self):
        self._running = False

        for task in self._current_tasks:
            task.stop()


class WrappedThreadPoolExecutor(ThreadPoolExecutor, EventReactorMixin):
    '''Wraps a :class:`.ThreadPoolExecutor` that listens to a stop event'''

    def __init__(self, max_workers, event_reactor):
        ThreadPoolExecutor.__init__(self, max_workers)
        EventReactorMixin.__init__(self, event_reactor)
        event_reactor.register_handler(EventReactor.STOP_ID, self._stop_cb)
        self._task_map = WeakValueDictionary()

    def _stop_cb(self, event_id):
        _logger.debug('WrappedThreadPoolExecutor stopping everything')

        for key in self._task_map.keys():
            self._task_map[key].stop()

        self.shutdown(wait=False)

    def submit(self, fn, *args, **kwargs):
        if isinstance(fn, Task):
            self._task_map[id(fn)] = fn

        return ThreadPoolExecutor.submit(self, fn, *args, **kwargs)


def asynchronous(daemon=True, name=None):
    '''Wrap a function to run in a separate thread'''

    def decorator(func):
        def wrapper(*args, **kwargs):
            @functools.wraps(func)
            def logged_func(*args, **kwargs):
                _logger.debug('Start async call %s',
                    threading.current_thread())

                try:
                    func(*args, **kwargs)
                except Exception as e:
                    _logger.exception('Error in async call')
                    raise e

                _logger.debug('Stop async call %s', threading.current_thread())

            thread = threading.Thread(target=logged_func, args=args,
                kwargs=kwargs)
            thread.daemon = daemon
            thread.name = name

            thread.start()

            return thread

        return wrapper
    return decorator
