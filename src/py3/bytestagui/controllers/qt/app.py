'''Application'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from PySide import QtGui # @UnresolvedImport
from bytestagui.controllers.base import BaseApplication
from bytestagui.controllers.config import ConfigController
from bytestagui.controllers.dht import DHTClientController
from bytestagui.controllers.qt.invoker import invoke_in_main_thread
from bytestagui.controllers.qt.main import MainWindowController
from bytestagui.controllers.qt.shareddirs import (SharedDirsScanController,
    SharedDirsTableController)
from bytestagui.controllers.qt.transfers import TransfersTableController
from bytestagui.controllers.qt.uiloader import UILoaderController
from bytestagui.controllers.shareddirs import SharedDirsController
import signal
import sys


class Application(BaseApplication):
    def __init__(self):
        BaseApplication.__init__(self)
        self.app = QtGui.QApplication(sys.argv)
        self.new_singleton(ConfigController)
        self.new_singleton(UILoaderController)
        self.new_singleton(DHTClientController)
        self.new_singleton(SharedDirsController)
        self.new_singleton(MainWindowController)
        self.new_singleton(SharedDirsScanController)
        self.new_singleton(SharedDirsTableController)
        self.new_singleton(TransfersTableController)

    def run(self):
        signal.signal(signal.SIGINT, self.stop)

        return self.app.exec_()

    def stop(self, *args):
        self.singletons[DHTClientController].stop()
        invoke_in_main_thread(self.app.quit)
