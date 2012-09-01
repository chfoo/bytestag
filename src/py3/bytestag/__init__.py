'''Wide Availability Peer-to-Peer File Sharing

Bytestag is a peer-to-peer (P2P) file sharing system that uses a distributed
hash table (DHT) to achieve wide availability of files. Unlike the BitTorrent
protocol, files are published entirely via DHT and do not require trackers
or swarming. Each computer donates disk space and bandwidth for caching of
published values.

This software is currently under development.
'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
import distutils.version

__docformat__ = 'restructuredtext en'
short_version = '0.2'  # N.N
__version__ = '0.2b1'  # N.N[.N]+[{a|b|c|rc}N[.N]+][.postN][.devN]
description, long_description = __doc__.split('\n', 1)
long_description = long_description.lstrip()

distutils.version.StrictVersion(__version__)
