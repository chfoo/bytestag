#!/usr/bin/env python
# encoding: utf-8
"""
    Tests for the bencode module
"""

__author__ = "Tom Lazar (tom@tomster.org)"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2007/07/29 $"
__copyright__ = "Copyright (c) 2007 Tom Lazar"
__license__ = "BitTorrent Open Source License"

# Python 3 port, UTF-8 support, PEP-8 compliance, implemented commented-
# out test cases, formatting by Christopher Foo :)

from .bencode import bencode
from .bencode import bdecode
from .bencode import BTFailure

import unittest


class KnownValues(unittest.TestCase):
    """
    * example values partially taken from
      http://en.wikipedia.org/wiki/Bencode
    * test case inspired by Mark Pilgrim's examples:
      http://diveintopython.org/unit_testing/romantest.html
    """
    knownValues = ((0, b'i0e'),
                    (1, b'i1e'),
                    (10, b'i10e'),
                    (42, b'i42e'),
                    (-42, b'i-42e'),
                    (True, b'i1e'),
                    (False, b'i0e'),
                    (b'spam', b'4:spam'),
                    (b'parrot sketch', b'13:parrot sketch'),
                    ([b'parrot sketch', 42], b'l13:parrot sketchi42ee'),

                    # Now thats UTF-8 testing!—Christopher Foo
                    ('ðÞở'.encode(), b'9:\xc3\xb0\xc3\x9e\xe1\xbb\x8f\xcc\x9b'),

                    ({
                        b'foo': 42,
                        b'bar': b'spam'
                    }, b'd3:bar4:spam3:fooi42ee'),
                  )

    def testBencodeKnownValues(self):
        """bencode should give known result with known input"""
        for plain, encoded in self.knownValues:
            result = bencode(plain)
            self.assertEqual(encoded, result)

    def testBdecodeKnownValues(self):
        """bdecode should give known result with known input"""
        for plain, encoded in self.knownValues:
            print(plain, encoded)
            result = bdecode(encoded)
            self.assertEqual(plain, result)

    def testRoundtripEncoded(self):
        """consecutive calls to bdecode and bencode should deliver the original
        data again
        """
        for plain, encoded in self.knownValues:
            result = bdecode(encoded)
            self.assertEqual(encoded, bencode(result))

    def testRoundtripDecoded(self):
        """consecutive calls to bencode and bdecode should deliver the original
        data again
        """
        for plain, encoded in self.knownValues:
            result = bencode(plain)
            self.assertEqual(plain, bdecode(result))


class IllegaleValues(unittest.TestCase):
    """ handling of illegal values"""

    def testFloatRaisesIllegalForEncode(self):
        """ floats cannot be encoded. """

        self.assertRaises(BTFailure, bencode, 1.0)

    def testNonStringsRaiseIllegalInputForDecode(self):
        """ non-strings should raise an exception. """

        self.assertRaises(BTFailure, bdecode, 0)
        self.assertRaises(BTFailure, bdecode, None)
        self.assertRaises(BTFailure, bdecode, 1.0)
        self.assertRaises(BTFailure, bdecode, [1, 2])
        self.assertRaises(BTFailure, bdecode, {'foo': 'bar'})

    def testRaiseIllegalInputForDecode(self):
        """illegally formatted strings should raise an exception when decoded.
        """
        self.assertRaises(BTFailure, bdecode, b"foo")
        self.assertRaises(BTFailure, bdecode, b"x:foo")
        self.assertRaises(BTFailure, bdecode, b"x42e")


class Dictionaries(unittest.TestCase):
    """ handling of dictionaries """

    def testSortedKeysForDicts(self):
        """ the keys of a dictionary must be sorted before encoded. """

        dict_ = {b'zoo': 42, b'bar': b'spam'}
        encoded_dict = bencode(dict_)
        self.failUnless(
            encoded_dict.index(b'zoo') > encoded_dict.index(b'bar'))

    def testNestedDictionary(self):
        """ tests for handling of nested dicts"""
        dict_ = {b'foo': 42, b'bar': {b'sketch': b'parrot', b'foobar': 23}}

        encoded_dict = bencode(dict_)
        self.assertEqual(encoded_dict,
            b"d3:bard6:foobari23e6:sketch6:parrote3:fooi42ee")


if __name__ == "__main__":
    unittest.main()
