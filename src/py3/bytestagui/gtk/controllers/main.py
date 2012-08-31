'''Main window'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from bytestagui.base.controllers.app import BaseController
from gi.repository import Gtk # @UnresolvedImport
import bytestagui
from bytestagui.gtk.controllers.inflater import InflaterController


class MainWindowController(BaseController):
    def __init__(self, application):
        BaseController.__init__(self, application)

        builder = self.application.singletons[InflaterController].main_builder
        self._builder = builder

        builder.connect_signals({
            'main_window_delete_event_cb': self._main_window_delete_event_cb,
            'main_window_destroy_cb': self._main_window_destroy_cb,
            'quit_menu_item_activate_cb': self._quit_menu_item_activate_cb,
            'about_menu_item_activate_cb': self._about_menu_item_activate_cb,
            'about_dialog_close_cb': self._about_dialog_close_cb,
            'about_dialog_response_cb': self._about_dialog_response_cb,
            'about_dialog_delete_event_cb': self._about_dialog_delete_event_cb,
        })

        window = builder.get_object('main_window')
        window.show_all()

        about_dialog = builder.get_object('about_dialog')
        about_dialog.set_version(bytestagui.__version__)

    def _main_window_delete_event_cb(self, *args):
        self.application.stop()

    def _main_window_destroy_cb(self, *args):
        self.application.stop()

    def _quit_menu_item_activate_cb(self, *args):
        self.application.stop()

    def _about_menu_item_activate_cb(self, *args):
        self._builder.get_object('about_dialog').show_all()

    def _about_dialog_close_cb(self, widget, *args):
        widget.hide()

    def _about_dialog_response_cb(self, widget, *args):
        widget.hide()

    def _about_dialog_delete_event_cb(self, widget, *args):
        return True
