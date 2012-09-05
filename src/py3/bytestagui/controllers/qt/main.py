'''Main window'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from PySide import QtGui
from bytestagui.controllers.base import BaseController
from bytestagui.controllers.dht import DHTClientController
from bytestagui.controllers.qt.invoker import invoke_in_main_thread
from bytestagui.controllers.qt.uiloader import UILoaderController
from bytestagui.views.dht import CONNECTING_MSG, CONNECTED_MSG, DISCONNECTED_MSG
import bytestagui


class MainWindowController(BaseController):
    '''Main window'''

    def __init__(self, application):
        BaseController.__init__(self, application)

        loader = self.application.singletons[UILoaderController]
        self._main_window = loader.main_window
        self._prefs_dialog = loader.preferences_dialog

        self._main_window.about_action.activated.connect(
            self._about_action_activated_cb)
        self._main_window.quit_action.activated.connect(self.application.stop)
        self._main_window.preferences_action.activated.connect(
            self._preferences_action_cb)
        self._main_window.shared_files_preferences_button.clicked.connect(
            self._shared_files_preferences_button_cb)

        self._dht_client = self.application.singletons[DHTClientController]

        def dht_client_cb(status):
            invoke_in_main_thread(self._dht_client_connect_cb, status)

        self._dht_client.observer.register(dht_client_cb)

        self._main_window.show()

    def _about_action_activated_cb(self, *args):
        QtGui.QMessageBox.about(self._main_window, 'About Bytestag Client UI',
            '<p><big><b>Bytestag Client UI</b></big></p>'
            '<p>{version_number}</p>'
            '<p><small>Copyright © 2012 Christopher Foo</small></p>'
            ''.format(version_number=bytestagui.__version__))

    def _dht_client_connect_cb(self, status):
        if status == DHTClientController.CONNECTING:
            self._main_window.main_status_bar.showMessage(CONNECTING_MSG)
        elif status == DHTClientController.CONNECTED:
            self._main_window.main_status_bar.showMessage(CONNECTED_MSG)
        else:
            self._main_window.main_status_bar.showMessage(DISCONNECTED_MSG)

    def _preferences_action_cb(self):
        self._prefs_dialog.show()

    def _shared_files_preferences_button_cb(self):
        self._prefs_dialog.tab_widget.setCurrentIndex(0)
        self._prefs_dialog.show()
