'''GtkBuilder'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from bytestagui.abstract.controllers.base import BaseController
from bytestagui.gtk.views.resource import Resource
from gi.repository import Gtk # @UnresolvedImport


class BuilderController(BaseController):
    def __init__(self, application):
        BaseController.__init__(self, application)
        builder = Gtk.Builder()
        self._builder = builder
        self._signals = {}

        builder.add_from_string(Resource.get_bytes('ui/main.glade').decode())

    @property
    def builder(self):
        return self._builder

    def add_signals(self, signal_dict):
        '''Adds signals to be connected.

        This method works around problem documented on
        http://stackoverflow.com/questions/6492000/
        '''

        self._signals.update(signal_dict)

    def connect_signals(self):
        self._builder.connect_signals(self._signals)
