from bytestag.uri import MagnetURI
from bytestag.keys import KeyBytes
import unittest


class TestMagnetURI(unittest.TestCase):
    def test_exact_target(self):
        uri = MagnetURI.parse('magnet:?xt=abcd')

        self.assertEqual(uri.exact_topic, 'abcd')

    def test_bittorrent_hash(self):
        uri = MagnetURI.parse(
            'magnet:?xt=urn:btih:DA39A3EE5E6B4B0D3255BFEF95601890AFD80709')

        self.assertEqual(uri.bittorent_info_hash, KeyBytes(
            'DA39A3EE5E6B4B0D3255BFEF95601890AFD80709'))

    def test_bytestag_hash(self):
        uri = MagnetURI.parse(
            'magnet:?xt=urn:bstagih:3I42H3S6NNFQ2MSVX7XZKYAYSCX5QBYJ')

        self.assertEqual(uri.bytestag_info_hash, KeyBytes(
            '3I42H3S6NNFQ2MSVX7XZKYAYSCX5QBYJ'))
