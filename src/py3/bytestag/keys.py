'''Keys'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from bytestag.lib.bitstring import Bits, BitArray
import base64
import binascii
import functools
import hashlib
import os

__docformat__ = 'restructuredtext en'


def leading_zero_bits(bytes_):
    '''Return the number of leading zero bits in ``bytes`` value.

    :rtype: `int`
    '''

    count = 0

    for char in Bits(bytes_).bin:
        if char == '0':
            count += 1
        else:
            break

    return count


def compute_bucket_number(key_1, key_2):
    '''Compute the bucket number for two keys.

    :Parameters:
        key_1: `KeyBytes`
            The first key
        key_2: `KeyBytes`
            The second key

    :rtype: `int`
    '''

    return leading_zero_bits(key_1.distance(key_2))


def random_bucket_key(node_key, bucket_number, bit_size=160):
    '''Return a key that corresponds to a given bucket number'''

    assert bucket_number < bit_size

    node_bits = Bits(node_key)
    bit_array = BitArray(os.urandom(bit_size // 8))

    bit_array.overwrite(node_bits[0:bucket_number + 1], 0)
    bit_array.invert(range(bucket_number, bucket_number + 1))

    return KeyBytes(bit_array.bytes)


def bytes_to_b64(b):
    '''Convert bytes to base64 string'''

    return base64.b64encode(b).decode()


def bytes_to_b32(b):
    '''Convert bytes to base32 string'''

    return base64.b32encode(b).decode()


def bytes_to_b16(b):
    '''Convert bytes to hex string'''

    return base64.b16encode(b).decode()


def b64_to_bytes(s, ignore_error=False):
    '''Convert base64 string to bytes'''

    if ignore_error:
        try:
            return base64.b64decode(s.encode())
        except binascii.Error:
            pass
    else:
        return base64.b64decode(s.encode())


def b32_to_bytes(s, ignore_error=False):
    '''Convert base32 string to bytes'''

    if ignore_error:
        try:
            return base64.b32decode(s.encode())
        except binascii.Error:
            pass
    else:
        return base64.b32decode(s.encode())


def b16_to_bytes(s, ignore_error=False):
    '''Convert hex string to bytes'''

    if ignore_error:
        try:
            return base64.b16decode(s.encode())
        except binascii.Error:
            pass
    else:
        return base64.b16decode(s.encode())


@functools.total_ordering
class KeyBytes(bytes):
    '''A fixed-width binary value that represents keys and node IDs'''

    BIT_SIZE = 160  # constant B

    def __new__(cls, o=True):
        '''Init

        :Parameters:
            obj: ``str`` or ``bytes``
                If ``str`` is provided, it may be in hex, base32 or base64.
        '''

        if isinstance(o, str):
            b = KeyBytes._from_str(o)
        elif isinstance(o, bytes):
            b = o
        elif o is True:
            b = os.urandom(KeyBytes.BIT_SIZE // 8)
        else:
            raise TypeError('Cannot parse')

        i = bytes.__new__(cls, b)
        i.validate()

        return i

    @classmethod
    def _from_str(cls, str_obj, as_base32=True, as_base64=True):
        '''Return bytes parsed from a ``str``.

        :Parameters:
            str_obj: ``str`` or ``bytes``
                If ``str`` is provided, it may be in hex, base32 or base64.
            as_base32: ``bool``
                If `True`, base32 values are accepted.
            as_base64: ``bool``
                If `True`, base64 values are accepted.
        '''

        try:
            return base64.b16decode(str_obj.encode(), True)
        except binascii.Error:
            pass

        if as_base32:
            try:
                return base64.b32decode(str_obj.encode(), True)
            except binascii.Error:
                pass

        if as_base64:
            try:
                return base64.b64decode(str_obj.encode())
            except binascii.Error:
                pass

        raise ValueError('Decoding binary number error')

    def validate(self):
        '''Check if the key is a valid size.

        :raise ValueError: Invalid bit size
        '''

        if len(self) != KeyBytes.BIT_SIZE // 8:
            raise ValueError('invalid bit size')

    @classmethod
    def new_silent(cls, value):
        '''Return a new `Key` instance if successfully parsed.

        :rtype: `Key`, ``None``
        '''

        try:
            return KeyBytes(value)
        except (ValueError, TypeError):
            pass

    @classmethod
    def new_hash(cls, bytes_):
        return KeyBytes(hashlib.sha1(bytes_).digest())

    @property
    def binary(self):
        '''Return the ``bytes`` representation.

        :rtype: ``bytes``
        '''

        return self

    @property
    def binary_str(self):
        '''Return the binary representation (zeros and ones).

        :rtype: ``str``
        '''

        return Bits(self).bin

    @property
    def integer(self):
        '''Return the integer representation.

        :rtype: ``int``
        '''

        return Bits(self).uintbe

    def __str__(self):
        return self.base16

    @property
    def base16(self):
        '''Return the hex representation.

        :rtype: ``str``
        '''

        return bytes_to_b16(self)

    @property
    def base32(self):
        '''Return the base 32 representation.

        :rtype: ``str``
        '''

        return bytes_to_b32(self)

    @property
    def base64(self):
        '''Return the base 64 representation.

        :rtype: ``str``
        '''

        return bytes_to_b64(self)

    def distance(self, other):
        '''Return the distance from another `Key`.

        :rtype: ``bytes``
        '''

        return (Bits(self) ^ Bits(other.binary)).bytes

    def distance_int(self, other):
        '''Return the distance from another `Key`.

        :rtype: ``int``
        '''

        return Bits(self.distance(other)).uintbe

    def __lt__(self, other):
        return self.integer < other.integer

    def validate_value(self, value):
        return self == hashlib.sha1(value).digest()

    @classmethod
    def validate_hash_value(cls, hash_bytes, value):
        return hash_bytes == hashlib.sha1(value).digest()
