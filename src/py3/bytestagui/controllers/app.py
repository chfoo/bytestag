from bytestagui.controllers.base import BaseApplication
from bytestagui.controllers.builder import BuilderController
from bytestagui.controllers.config import ConfigController
from bytestagui.controllers.dht import DHTClientController
from bytestagui.controllers.main import MainWindowController
from bytestagui.controllers.sharedfiles import SharedFilesController
from bytestagui.controllers.transfers import TransfersTabController
from gi.repository import Gtk, Gdk, GLib # @UnresolvedImport
import signal
import sys


class Application(BaseApplication):
    def __init__(self):
        BaseApplication.__init__(self)
        self.new_singleton(BuilderController)
        self.new_singleton(ConfigController)
        self.new_singleton(MainWindowController)
        self.new_singleton(DHTClientController)
        self.new_singleton(SharedFilesController)
        self.new_singleton(TransfersTabController)

        self.singletons[BuilderController].connect_signals()
        self.run()

    def run(self):
        # GNOME bug #622084:
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        GLib.threads_init()
        Gdk.threads_init()
        Gdk.threads_enter()
        Gtk.main()
        Gdk.threads_leave()

    def stop(self):
        Gtk.main_quit()

        # FIXME: properly terminate threads
        sys.exit(0)
