from bytestag.queue import BigDiskQueue
import random
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

    def test_queue_random(self):
        '''It should add n and return n items randomly'''

        self.maxDiff = None

        q = BigDiskQueue(memory_size=10)
        n = 100
        num_puts = 0
        num_gets = 0

        q.put(num_puts)

        num_puts += 1

        rand = random.Random()
        rand.seed(0)

        l = []

        while num_gets < n:
            if num_puts < n and rand.randint(0, 1):
                q.put(num_puts)

                num_puts += 1

            if num_puts > num_gets and rand.random() < 0.3:
                    l.append(q.get(timeout=1))

                    num_gets += 1

        self.assertEqual(n, len(l))
        self.assertEqual(list(range(0, n)), list(sorted(l)))

