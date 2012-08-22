from bytestag.ui.controllers.base import BaseApplication
from bytestag.ui.controllers.builder import BuilderController
from bytestag.ui.controllers.config import ConfigController
from bytestag.ui.controllers.dht import DHTClientController
from bytestag.ui.controllers.main import MainWindowController
from bytestag.ui.controllers.sharedfiles import SharedFilesController
from bytestag.ui.controllers.transfers import TransfersTabController
from gi.repository import Gtk, Gdk, GLib # @UnresolvedImport
import signal


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


