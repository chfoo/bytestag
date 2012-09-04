'''QtUiLoader'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from PySide import QtCore, QtUiTools # @UnresolvedImport
from bytestagui.controllers.base import BaseController
from bytestagui.views.qt.resource import Resource


class UILoaderController(BaseController):
    '''Provides access to :class:`.QUiLoader`'''

    def __init__(self, application):
        BaseController.__init__(self, application)
        self.main_window = self.load_widget('ui/main.ui')
        self.preferences_dialog = self.load_widget('ui/preferences.ui')
        self.open_link_dialog = self.load_widget('ui/open_link.ui')

    def load_widget(self, resource_name):
        loader = QtUiTools.QUiLoader()
        qt_file = QtCore.QBuffer()

        qt_file.open(QtCore.QBuffer.ReadWrite)
        qt_file.write(Resource.get_bytes(resource_name))
        qt_file.seek(0)

        return loader.load(qt_file)
