from bytestagui.controllers.base import BaseController
from bytestagui.controllers.builder import BuilderController
from gi.repository import Gtk # @UnresolvedImport
import bytestag


class MainWindowController(BaseController):
    def __init__(self, application):
        BaseController.__init__(self, application)

        builder = self.application.singletons[BuilderController].builder
        self._builder = builder

        self.application.singletons[BuilderController].add_signals({
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
        about_dialog.set_version(bytestag.__version__)

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
