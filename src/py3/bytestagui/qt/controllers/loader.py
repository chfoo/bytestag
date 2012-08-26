'''QtUiLoader'''
from PySide import QtCore, QtUiTools
from bytestagui.abstract.controllers.base import BaseController
from bytestagui.qt.controllers.invoker import invoke_in_main_thread
from bytestagui.qt.views.resource import Resource


class LoaderController(BaseController):
    def __init__(self, application):
        BaseController.__init__(self, application)
        self._main_window = self.load_widget('ui/main.ui')

    def load_widget(self, resource_name):
        loader = QtUiTools.QUiLoader()
        qt_file = QtCore.QBuffer()

        qt_file.open(QtCore.QBuffer.ReadWrite)
        qt_file.write(Resource.get_bytes(resource_name))
        qt_file.seek(0)

        return loader.load(qt_file)

    @property
    def main_window(self):
        return self._main_window

    def connect(self, signal, slot):
        def f(*args, **kwargs):
            invoke_in_main_thread(slot, *args, **kwargs)

        signal.connect(f)
