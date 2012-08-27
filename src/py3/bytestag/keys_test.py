'''KeyBytes value testing'''
from bytestag.lib.bitstring import Bits
from bytestag.keys import (KeyBytes, leading_zero_bits, compute_bucket_number,
    random_bucket_key, bytes_to_b64, bytes_to_b32, bytes_to_b16, b64_to_bytes,
    b32_to_bytes, b16_to_bytes)
import unittest


class TestKeyBytes(unittest.TestCase):
    def test_valid_id(self):
        '''It should not raise error on valid id'''

        KeyBytes('00' * 20)
        KeyBytes(b'\x00' * 20)

    def test_bad_length(self):
        '''It should raise ValueError on invalid id'''

        def f1():
            KeyBytes('00' * 10)

        def f2():
            KeyBytes(b'\x00' * 25)

        self.assertRaises(ValueError, f1)
        self.assertRaises(ValueError, f2)

    def test_serialize(self):
        '''It should return a hex string'''

        self.assertEqual(str(KeyBytes('00' * 20)), '00' * 20)

    def test_equality(self):
        '''It should be equal if the id is the same'''

        n1 = KeyBytes('BEE2286934E868F0043EB0856D15C03F72AAAD8B')
        n2 = KeyBytes('BEE2286934E868F0043EB0856D15C03F72AAAD8B')
        n3 = KeyBytes('3E4FF22E9E8B92CFCEBC10D8445EB3DE85D93DB9')

        self.assertEqual(n1, n2)
        self.assertNotEqual(n1, n3)

    def test_random_bucket_key(self):
        '''It should generate keys that goes into given bucket number'''

        node_key = KeyBytes()

        for i in range(160):
            key = random_bucket_key(node_key, i)

            self.assertEqual(i, compute_bucket_number(node_key, key))


class TestFunctions(unittest.TestCase):
    def test_leading_zero_bits(self):
        '''It should count the leading zeros bits'''

        self.assertEqual(leading_zero_bits(Bits('0b11111111').bytes), 0)
        self.assertEqual(leading_zero_bits(Bits('0b01111111').bytes), 1)
        self.assertEqual(leading_zero_bits(Bits('0b00111111').bytes), 2)
        self.assertEqual(leading_zero_bits(Bits('0b00010000').bytes), 3)

    def test_compute_bucket_number(self):
        '''It should return the bucket number based on leading zeros bits'''

        self.assertEqual(compute_bucket_number(
            KeyBytes('00' * 20), KeyBytes('00' * 20)), 160)
        self.assertEqual(compute_bucket_number(
            KeyBytes('00' * 20), KeyBytes('FF' * 20)), 0)
        self.assertEqual(compute_bucket_number(
            KeyBytes('00' * 20), KeyBytes('00' * 10 + 'FF' * 10)), 80)


class TestByteConvertion(unittest.TestCase):
    def test_conversion(self):
        self.assertEqual(bytes_to_b64(b'\xdd'), '3Q==')
        self.assertEqual(bytes_to_b32(b'\xdd'), '3U======')
        self.assertEqual(bytes_to_b16(b'\xdd'), 'DD')
        self.assertEqual(b64_to_bytes('3Q=='), b'\xdd')
        self.assertEqual(b32_to_bytes('3U======'), b'\xdd')
        self.assertEqual(b16_to_bytes('DD'), b'\xdd')

    def test_silent_conversion(self):
        self.assertFalse(b64_to_bytes('A', ignore_error=True))
        self.assertFalse(b32_to_bytes('$', ignore_error=True))
        self.assertFalse(b16_to_bytes('$', ignore_error=True))
