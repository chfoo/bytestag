'''Wide Availability Peer-to-Peer File Sharing Client

This package provides a graphical user interface GUI to the Bytestag
network. It includes interfaces written for GTK+3 (via PyGObject) and
Qt (via PySide)'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
import distutils.version
import bytestag

__docformat__ = 'restructuredtext en'
short_version = bytestag.short_version  # N.N
__version__ = bytestag.__version__  # N.N[.N]+[{a|b|c|rc}N[.N]+][.postN][.devN]
description, long_description = __doc__.split('\n', 1)
long_description = long_description.lstrip()

distutils.version.StrictVersion(__version__)
