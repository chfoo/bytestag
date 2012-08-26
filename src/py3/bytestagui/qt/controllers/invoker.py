'''Call functions on main thread.

See `<http://stackoverflow.com/questions/10991991>`_
'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from PySide import QtCore # @UnresolvedImport
import threading


class InvokeEvent(QtCore.QEvent):
    EVENT_TYPE = QtCore.QEvent.Type(QtCore.QEvent.registerEventType())

    def __init__(self, fn, *args, **kwargs):
        QtCore.QEvent.__init__(self, InvokeEvent.EVENT_TYPE)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs


class Invoker(QtCore.QObject):
    def event(self, event):
        event.fn(*event.args, **event.kwargs)

        return True

_invoker = Invoker()


def invoke_in_main_thread(fn, *args, **kwargs):
    assert fn

    QtCore.QCoreApplication.postEvent(_invoker,
        InvokeEvent(fn, *args, **kwargs))
