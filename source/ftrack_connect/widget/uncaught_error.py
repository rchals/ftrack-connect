# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import sys
import traceback
import cStringIO
import logging

from PySide import QtGui, QtCore


class UncaughtError(QtGui.QMessageBox):
    '''Widget that handles uncaught errors and presents a message box.'''

    onError = QtCore.Signal(object, object, object)

    def __init__(self, *args, **kwargs):
        '''Initialise and setup widget.'''
        super(UncaughtError, self).__init__(*args, **kwargs)
        self.setIcon(QtGui.QMessageBox.Critical)
        self.onError.connect(self.exceptHook)

        # Listen to all unhandled exceptions.
        sys.excepthook = self.onError.emit

    def getTraceback(self, exceptionTraceback):
        '''Return message from *exceptionTraceback*.'''
        tracebackInfoStream = cStringIO.StringIO()
        traceback.print_tb(
            exceptionTraceback,
            None,
            tracebackInfoStream
        )
        tracebackInfoStream.seek(0)
        return tracebackInfoStream.read()

    def exceptHook(self, exceptionType, exceptionValue, exceptionTraceback):
        '''Show message box with error details.'''

        logging.error(
            'Logging an uncaught exception',
            exc_info=(exceptionType, exceptionValue, exceptionTraceback)
        )

        # Show exception to user.
        tracebackInfo = self.getTraceback(exceptionTraceback)
        self.setDetailedText(tracebackInfo)

        # Make sure text is at least a certain length to force message box size.
        # Otherwise buttons will not fit.
        self.setText(str(exceptionValue).ljust(50, ' '))
        self.exec_()

    def resizeEvent(self, event):
        '''Hook into the resize *event* and force width of detailed text.'''
        result = super(UncaughtError, self).resizeEvent(event)

        detailsBox = self.findChild(QtGui.QTextEdit)
        if detailsBox is not None:
            detailsBox.setFixedSize(500, 200)

        return result
