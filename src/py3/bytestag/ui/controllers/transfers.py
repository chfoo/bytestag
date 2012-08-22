from bytestag.dht.network import StoreValueTask, StoreToNodeTask
from bytestag.ui.controllers.base import BaseController
from bytestag.ui.controllers.builder import BuilderController
from bytestag.ui.controllers.dht import DHTClientController
from gi.repository import Gtk, GLib # @UnresolvedImport


class TransfersTabController(BaseController):
    def __init__(self, application):
        BaseController.__init__(self, application)
        self._builder = self.application.singletons[BuilderController].builder
        self._task_to_tree_iter_map = {}

        self._create_tree_view_columns()
        self._connect_upload_slot()

        GLib.timeout_add(200, self._update_progress)

    def _create_tree_view_columns(self):
        builder = self._builder
        transfers_tree_view = builder.get_object('transfers_tree_view')

        type_pixbuf_renderer = Gtk.CellRendererPixbuf()
        type_column = Gtk.TreeViewColumn('', type_pixbuf_renderer, stock_id=0)

        transfers_tree_view.append_column(type_column)

        address_column = Gtk.TreeViewColumn('Address')
        host_cell_renderer = Gtk.CellRendererText()
        port_cell_renderer = Gtk.CellRendererText()
        address_column.pack_start(host_cell_renderer, False)
        address_column.pack_start(port_cell_renderer, False)
        address_column.add_attribute(host_cell_renderer, 'text', 1)
        address_column.add_attribute(port_cell_renderer, 'text', 2)

        transfers_tree_view.append_column(address_column)

        key_cell_renderer = Gtk.CellRendererText()
        key_column = Gtk.TreeViewColumn('Key', key_cell_renderer, text=3)

        key_column.set_resizable(True)
        transfers_tree_view.append_column(key_column)

        progress_cell_renderer = Gtk.CellRendererProgress()
        progress_column = Gtk.TreeViewColumn('Progress',
            progress_cell_renderer, value=6)

        transfers_tree_view.append_column(progress_column)

    def _connect_upload_slot(self):
        builder = self._builder
        upload_slot = self.application.singletons[
            DHTClientController].client.upload_slot
        transfers_list_store = builder.get_object('transfers_list_store')

        def store_to_node_task_cb(added, task):
            assert isinstance(task, StoreToNodeTask)

            if added:
                tree_iter = transfers_list_store.append([
                    # FIXME: provide real icons
                    Gtk.STOCK_GO_UP,
                    task.node.address[0],
                    task.node.address[1],
                    '{}:{}'.format(task.key.base32, task.index.base32).lower(),
                    task.progress,
                    task.total_size,
                    0,
                ])

                self._task_to_tree_iter_map[task] = tree_iter
            else:
                tree_iter = self._task_to_tree_iter_map.pop(task)
                transfers_list_store.remove(tree_iter)

        def upload_slot_callback(added, task):
            assert isinstance(task, StoreValueTask)

            task.store_to_node_task_observer.register(
                 lambda *args: GLib.idle_add(store_to_node_task_cb, *args))

        upload_slot.observer.register(upload_slot_callback)

    def _update_progress(self):
        transfers_list_store = self._builder.get_object('transfers_list_store')

        for task, tree_iter in self._task_to_tree_iter_map.items():
            if isinstance(task, StoreToNodeTask):
                if task.progress:
                    transfers_list_store[tree_iter][4] = task.progress
                    transfers_list_store[tree_iter][6] = \
                        int(task.progress / task.total_size * 100)

        return True
