'''Application entry point with qt as default'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
import bytestagui.main
from PySide import QtCore, QtGui  # @UnresolvedImport @UnusedImport


if __name__ == '__main__':
    bytestagui.main.main(default_gui='qt')
