#!/usr/bin/env python3

import os
import sys
from distutils.core import setup

src_dir = os.path.abspath(os.path.join('src', 'py3'))
sys.path.insert(0, src_dir)

import bytestag

setup(name='Bytestag',
    version=bytestag.__version__,
    description=bytestag.description,
    long_description=bytestag.long_description,
    author='Christopher Foo',
    author_email='chris.foo@gmail.com',
#    url='',
    packages=['bytestag'],
    package_dir={'': src_dir},
    classifiers=[
        'Development Status :: 1 - Planning',
        'Operating System :: OS Independent',
        'Topic :: Internet',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
    ],
    requires=['bitstring (3.0)',]
)
