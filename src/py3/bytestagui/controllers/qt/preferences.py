'''Preferences window'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from bytestagui.controllers.base import BaseController
from bytestagui.controllers.config import ConfigController
from bytestagui.controllers.qt.uiloader import UILoaderController
from PySide import QtGui, QtCore # @UnresolvedImport


class PreferencesController(BaseController):
    '''Controls setting prefs for listening address and storage tabs'''

    def __init__(self, application):
        BaseController.__init__(self, application)

        self._config = self.application.singletons[ConfigController]
        loader = self.application.singletons[UILoaderController]
        self._prefs_dialog = loader.preferences_dialog

        self._populate_form()

        self._prefs_dialog.listening_host_edit.editingFinished.connect(
            self._save_config_cb)
        self._prefs_dialog.listening_port_spin_box.valueChanged.connect(
            self._save_config_cb)
        self._prefs_dialog.cache_max_size_spin_box.valueChanged.connect(
            self._save_config_cb)

        self._prefs_dialog.button_box.clicked.connect(
            self._button_box_clicked_cb)
        self._prefs_dialog.default_share_dir_button.clicked.connect(
            self._default_share_dir_button_cb)

    def _populate_form(self):
        self._prefs_dialog.listening_host_edit.setText(
            self._config.get('network', 'host'))
        self._prefs_dialog.listening_port_spin_box.setValue(
            int(self._config.get('network', 'port')))
        self._prefs_dialog.cache_max_size_spin_box.setValue(
            int(self._config.get('cache', 'max_size')) // 1048576)
        self._prefs_dialog.default_share_dir_button.setText(
            self._config.get('sharing', 'default_share_dir'))

    def _save_config_cb(self):
        self._config.set('network', 'host',
            self._prefs_dialog.listening_host_edit.text())
        self._config.set('network', 'port',
            self._prefs_dialog.listening_port_spin_box.value())
        self._config.set('cache', 'max_size',
            self._prefs_dialog.cache_max_size_spin_box.value() * 1048576)

        self._config.save()

    @QtCore.Slot(QtGui.QAbstractButton)
    def _button_box_clicked_cb(self, button):
        role = self._prefs_dialog.button_box.buttonRole(button)

        if role == QtGui.QDialogButtonBox.ResetRole:
            self._reset_defaults(self._prefs_dialog.tab_widget.currentIndex())

    def _default_share_dir_button_cb(self):
        dialog = QtGui.QFileDialog(self._prefs_dialog, 'Select a folder')
        dialog.setFileMode(QtGui.QFileDialog.Directory)

        if not dialog.exec_():
            return

        filenames = dialog.selectedFiles()

        self._config.set('sharing', 'default_share_dir', filenames[0])
        self._config.save()
        self._populate_form()

    def _reset_defaults(self, index):
        if index == 1:
            self._config.set_default('network', 'host')
            self._config.set_default('network', 'port')
        elif index == 2:
            self._config.set_default('cache', 'max_size')
            self._config.set_default('sharing', 'default_share_dir')

        self._config.save()

        self._populate_form()
