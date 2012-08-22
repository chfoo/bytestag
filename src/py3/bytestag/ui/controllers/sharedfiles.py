from bytestag.ui.controllers.base import BaseController
from bytestag.ui.controllers.builder import BuilderController
from bytestag.ui.controllers.config import ConfigController
from bytestag.ui.controllers.dht import DHTClientController
from gi.repository import Gtk, GLib # @UnresolvedImport


class SharedFilesController(BaseController):
    def __init__(self, application):
        BaseController.__init__(self, application)
        self._builder = self.application.singletons[BuilderController].builder
        self._paths_shown = set()
        self._scan_task = None

        self.application.singletons[BuilderController].add_signals({
            'shared_files_add_button_clicked_cb':
                self._shared_files_add_button_clicked_cb,
            'shared_files_remove_button_clicked_cb':
                self._shared_files_remove_button_clicked_cb,
            'shared_files_scan_button_clicked_cb':
                self._shared_files_scan_button_clicked_cb,
            'shared_files_scan_stop_button_clicked_cb':
                self._shared_files_scan_stop_button_clicked_cb,
            'shared_files_file_chooser_dialog_close_cb':
                self._shared_files_file_chooser_dialog_close_cb,
            'shared_files_file_chooser_dialog_response_cb':
                self._shared_files_file_chooser_dialog_response_cb,
            'shared_files_file_chooser_dialog_delete_event_cb':
                self._shared_files_file_chooser_dialog_delete_event_cb,
            'shared_files_tree_view_cursor_changed_cb':
                self._shared_files_tree_view_cursor_changed_cb,
        })

        self._disable_scan_ui()
        self._create_tree_view_columns()
        self._load_shared_files_config()

    def _create_tree_view_columns(self):
        builder = self._builder
        shared_files_tree_view = builder.get_object('shared_files_tree_view')

        path_cell_renderer = Gtk.CellRendererText()
        path_column = Gtk.TreeViewColumn('Folder', path_cell_renderer,
            text=0)

        shared_files_tree_view.append_column(path_column)

    def _disable_scan_ui(self):
        self._builder.get_object('shared_files_scan_box').hide()
        self._builder.get_object('shared_files_scan_button'
            ).set_sensitive(True)
        self._builder.get_object('shared_files_scan_spinner').stop()

        if self._scan_task:
            assert self._scan_task.is_finished

        self._scan_task = None

    def _enable_scan_ui(self):
        self._builder.get_object('shared_files_scan_box').show_all()
        self._builder.get_object('shared_files_scan_button'
            ).set_sensitive(False)
        self._builder.get_object('shared_files_scan_spinner').start()

    def _shared_files_add_button_clicked_cb(self, *args):
        self._builder.get_object('shared_files_file_chooser_dialog').show_all()

    def _shared_files_remove_button_clicked_cb(self, *args):
        shared_files_tree_view = self._builder.get_object(
            'shared_files_tree_view')
        selection = shared_files_tree_view.get_selection()
        model, tree_iter = selection.get_selected()
        path = model[tree_iter][0]

        directories = self.application.singletons[DHTClientController
            ].client.shared_files_table.shared_directories
        directories.remove(path)
        self._paths_shown.remove(path)
        del model[tree_iter]
        self._save_shared_files_config()

    def _shared_files_scan_button_clicked_cb(self, widget, *args):
        self._enable_scan_ui()
        self._scan_task = self.application.singletons[
            DHTClientController].client.shared_files_table.hash_directories()

        def f(*args):
            GLib.idle_add(self._disable_scan_ui)

        self._scan_task.observer.register(f)
        GLib.timeout_add(200, self._update_scan_progress)

    def _shared_files_scan_stop_button_clicked_cb(self, *args):
        def f(*args):
            GLib.idle_add(self._disable_scan_ui)

        self._scan_task.observer.register(f)
        self._scan_task.stop()

    def _shared_files_file_chooser_dialog_response_cb(self, widget,
    response_id, *args):
        widget.hide()
        if response_id == 1:
            for path in widget.get_filenames():
                self._add_directory(path)

            self._save_shared_files_config()

    def _shared_files_file_chooser_dialog_close_cb(self, widget, *args):
        widget.hide()

    def _shared_files_file_chooser_dialog_delete_event_cb(self, *args):
        return True

    def _add_directory(self, path):
        directories = self.application.singletons[
            DHTClientController].client.shared_files_table.shared_directories

        if path not in directories:
            directories.append(path)

        self._populate_tree_view()

    def _populate_tree_view(self):
        directories = self.application.singletons[
            DHTClientController].client.shared_files_table.shared_directories
        list_store = self._builder.get_object('shared_files_list_store')

        for path in directories:
            if path not in self._paths_shown:
                self._paths_shown.add(path)
                list_store.append([path])

    def _load_shared_files_config(self):
        config_parser = self.application.singletons[
            ConfigController].config_parser
        directories = self.application.singletons[
            DHTClientController].client.shared_files_table.shared_directories

        for key in config_parser['shared_files'].keys():
            directories.append(config_parser['shared_files'][key])

        self._populate_tree_view()

    def _save_shared_files_config(self):
        config_parser = self.application.singletons[
            ConfigController].config_parser
        directories = self.application.singletons[
            DHTClientController].client.shared_files_table.shared_directories

        config_parser['shared_files'] = {}

        for i in range(len(directories)):
            directory = directories[i]

            config_parser['shared_files']['path{}'.format(i)] = directory

        self.application.singletons[ConfigController].save()

    def _update_scan_progress(self):
        if self._scan_task:
            filename, bytes_read = self._scan_task.progress
            shared_files_scan_label = self._builder.get_object(
                'shared_files_scan_label')

            # FIXME: l10n support
            shared_files_scan_label.set_text('Scanning file {} ({})'.format(
                filename, bytes_read))

            return True

    def _shared_files_tree_view_cursor_changed_cb(self, tree_view, *args):
        shared_files_tree_view = self._builder.get_object(
            'shared_files_tree_view')
        selection = shared_files_tree_view.get_selection()

        if selection:
            sensitive = True if selection.get_selected()[1] else False
        else:
            sensitive = False

        self._builder.get_object('shared_files_remove_button').set_sensitive(
            sensitive)

