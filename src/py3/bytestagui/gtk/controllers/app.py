'''Application'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from bytestagui.base.controllers.app import BaseApplication
from bytestagui.gtk.controllers.config import ConfigController
from bytestagui.gtk.controllers.dht import DHTClientController
from bytestagui.gtk.controllers.inflater import InflaterController
from bytestagui.gtk.controllers.main import MainWindowController
#from bytestagui.gtk.controllers.sharedfiles import SharedFilesController
#from bytestagui.gtk.controllers.transfers import TransfersTabController
from gi.repository import Gtk, Gdk, GLib # @UnresolvedImport
import signal


class Application(BaseApplication):
    def __init__(self):
        BaseApplication.__init__(self)
        self.new_singleton(InflaterController)
        self.new_singleton(ConfigController)
        self.new_singleton(MainWindowController)
        self.new_singleton(DHTClientController)
#        self.new_singleton(SharedFilesController)
#        self.new_singleton(TransfersTabController)

    def run(self):
        signal.signal(signal.SIGINT, self.stop)

        GLib.threads_init()
        Gdk.threads_init()
        Gdk.threads_enter()
        Gtk.main()
        Gdk.threads_leave()

    def stop(self, *args):
        self.singletons[DHTClientController].stop()
        Gtk.main_quit()
