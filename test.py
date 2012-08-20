#!/usr/bin/env python3

import logging
import sys
import os.path
import unittest

def main():
#    logging.basicConfig(level=logging.DEBUG)
    test_loader = unittest.TestLoader()
    tests = test_loader.discover(os.path.join('src', 'py3'), '*_test.py')
    test_runner = unittest.TextTestRunner()
    test_runner.run(tests)

if __name__ == '__main__':
    main()
