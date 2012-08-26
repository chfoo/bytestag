'''Main window'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from PySide import QtGui, QtCore
from bytestagui.abstract.controllers.base import BaseController
from bytestagui.qt.controllers.loader import LoaderController
import bytestagui


class MainWindowController(BaseController):
    def __init__(self, application):
        BaseController.__init__(self, application)

        main_window = self.application.singletons[LoaderController].main_window
        self._main_window = main_window

        main_window.about_action.activated.connect(
            self._about_action_activated_cb)

        main_window.show()

    def _about_action_activated_cb(self, *args):
        QtGui.QMessageBox.about(self._main_window, 'About Bytestag UI',
            '<p><big><b>Bytestag UI</b></big></p>'
            '<p>{version_number}</p>'
            '<p><small>Copyright © 2012 Christopher Foo</small></p>'
            ''.format(version_number=bytestagui.__version__))
