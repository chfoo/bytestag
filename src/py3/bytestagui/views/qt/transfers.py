'''Transfers'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from PySide import QtGui, QtCore


class TransferTableViewDelegate(QtGui.QItemDelegate):
    def sizeHint(self, option, index):
        return QtCore.QSize(120, 30)

    def paint(self, painter, option, index):
        if index.column() != 3:
            QtGui.QItemDelegate.paint(self, painter, option, index)

            return

        progress_bar_option = QtGui.QStyleOptionProgressBarV2()
        progress_bar_option.state = QtGui.QStyle.State_Enabled
        progress_bar_option.direction = QtGui.QApplication.layoutDirection()
        progress_bar_option.fontMetrics = QtGui.QApplication.fontMetrics()
        progress_bar_option.minimum = 0
        progress_bar_option.maximum = 100
        progress_bar_option.progress = int(index.data() * 100)
        progress_bar_option.rect = option.rect
        progress_bar_option.textVisible = True
        progress_bar_option.text = '{}%'.format(int(index.data() * 100))

        QtGui.QApplication.style().drawControl(QtGui.QStyle.CE_ProgressBar,
            progress_bar_option, painter)
