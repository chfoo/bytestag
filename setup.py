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
    url='https://launchpad.net/bytestag',
    packages=['bytestag', 'bytestag.dht', 
        'bytestag.ui', 'bytestag.ui.controllers', 'bytestag.ui.models',
        'bytestag.ui.views',
    ],
    package_dir={'': src_dir},
    package_data={
        'bytestag.ui.views': ['ui/*.glade']
    },
    classifiers=[
        'Development Status :: 1 - Planning',
        'Operating System :: OS Independent',
        'Topic :: Internet',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
    ],
    requires=['bitstring (>=3.0)',]
)
