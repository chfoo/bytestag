from bytestag.queue import BigDiskQueue
import unittest


class TestBigDiskQueue(unittest.TestCase):
    def test_queue(self):
        '''It should add n and return n items'''

        q = BigDiskQueue(memory_size=10)
        n = 100

        for i in range(n):
            q.put(i)

        count = 0

        for i in range(n):
            item = q.get(timeout=1)  # @UnusedVariable
            count += 1

        self.assertEqual(count, n)
