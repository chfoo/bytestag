from bytestag.files import safe_filename
import os
import unittest


class TestSafeFilename(unittest.TestCase):
    def test_parent_directory(self):
        '''It should raise error for parent directory'''

        self.assertRaises(ValueError, safe_filename, os.pardir)

    def test_seperators(self):
        '''It should replace path separators'''

        self.assertEqual(safe_filename('a/b', 'Linux'), 'a_b')
        self.assertEqual(safe_filename('a/b', 'Windows'), 'a_b')
        self.assertEqual(safe_filename('a\\b', 'Windows'), 'a_b')

    def test_invalid_windows_filename(self):
        '''It should raise error on invalid windows name'''

        self.assertRaises(ValueError, safe_filename, 'CON.txt', 'Windows')
        self.assertRaises(ValueError, safe_filename, 'NUL', 'Windows')
        self.assertRaises(ValueError, safe_filename, 'LPT9', 'Windows')
        self.assertRaises(ValueError, safe_filename, 'hello.', 'Windows')

    def test_invalid_chars(self):
        '''It should replace invalid chars'''

        self.assertEqual(safe_filename('\x00abc', 'Linux'), '_abc')
        self.assertEqual(safe_filename('\x00abc', 'Windows'), '_abc')
        self.assertEqual(safe_filename('"abc:"', 'Windows'), '_abc__')

