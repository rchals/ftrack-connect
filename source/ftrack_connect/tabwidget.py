# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

from PySide import QtGui


class TabWidget(QtGui.QTabWidget):
    def __init__(self, *args, **kwargs):
        '''Instantiate the tab widget.'''
        QtGui.QTabWidget.__init__(self, *args, **kwargs)
