'''GtkBuilder'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from bytestagui.base.controllers.inflater import BaseInflaterController
from bytestagui.gtk.views.resource import Resource
from gi.repository import Gtk # @UnresolvedImport


class InflaterController(BaseInflaterController):
    def __init__(self, application):
        BaseInflaterController.__init__(self, application)
        self.main_builder = self.load('ui/main.glade')

    def load(self, name):
        builder = Gtk.Builder()

        builder.add_from_string(Resource.get_bytes(name).decode())

        return builder
