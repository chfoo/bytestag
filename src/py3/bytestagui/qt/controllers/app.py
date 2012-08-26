'''Application'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from PySide import QtGui  # @UnresolvedImport
from bytestagui.abstract.controllers.config import ConfigController
from bytestagui.qt.controllers.dht import DHTClientController
from bytestagui.qt.controllers.loader import LoaderController
from bytestagui.qt.controllers.main import MainWindowController
from bytestagui.qt.controllers.sharedfiles import SharedFilesController
from bytestagui.qt.controllers.transfers import TransfersTabController
import bytestagui.abstract.controllers.app
import signal
import sys
from bytestagui.qt.controllers.invoker import invoke_in_main_thread


class Application(bytestagui.abstract.controllers.app.Application):
    def __init__(self):
        bytestagui.abstract.controllers.app.Application.__init__(self)
        self.app = QtGui.QApplication(sys.argv)
        self.new_singleton(ConfigController)
        self.new_singleton(LoaderController)
        self.new_singleton(MainWindowController)
        self.new_singleton(DHTClientController)
        self.new_singleton(SharedFilesController)
        self.new_singleton(TransfersTabController)

    def run(self):
        # FIXME: can't control+c
        signal.signal(signal.SIGINT,
            lambda *dummy: invoke_in_main_thread(self.stop))

        sys.exit(self.app.exec_())

    def stop(self):
        self.app.quit()
