'''QtUiLoader'''
from bytestagui.abstract.controllers.base import BaseController
from bytestagui.qt.views.resource import Resource
import PySide.QtCore
import PySide.QtUiTools


class LoaderController(BaseController):
    def __init__(self, application):
        BaseController.__init__(self, application)

        buf = PySide.QtCore.QBuffer(Resource.get_bytes('ui/main.ui'))
        self._loader = PySide.QtUiTools.QUiLoader()
        self._loader.load(buf)

    @property
    def loader(self):
        return self._loader
