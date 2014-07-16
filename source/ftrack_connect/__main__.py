# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import argparse
import logging
import sys
import signal
import os

from PySide import QtGui


# Hooks use the ftrack event system. Set the FTRACK_TOPIC_PLUGIN_PATH
# to pick up the default hooks if it has not already been set.
os.environ.setdefault(
    'FTRACK_TOPIC_PLUGIN_PATH',
    os.path.abspath(
        os.path.join(
            os.path.realpath(__file__), '..', '..', '..', 'resource', 'hooks'
        )
    )
)

import ftrack_connect.ui.application
import ftrack_connect.ui.theme


def main(arguments=None):
    '''ftrack connect.'''
    if arguments is None:
        arguments = []

    parser = argparse.ArgumentParser()

    # Allow setting of logging level from arguments.
    loggingLevels = {}
    for level in (
        logging.NOTSET, logging.DEBUG, logging.INFO, logging.WARNING,
        logging.ERROR, logging.CRITICAL
    ):
        loggingLevels[logging.getLevelName(level).lower()] = level

    parser.add_argument(
        '-v', '--verbosity',
        help='Set the logging output verbosity.',
        choices=loggingLevels.keys(),
        default='info'
    )

    parser.add_argument(
        '-t', '--theme',
        help='Set the theme to use.',
        choices=['light', 'dark'],
        default='light'
    )

    namespace = parser.parse_args(arguments)

    logging.basicConfig(level=loggingLevels[namespace.verbosity])

    # Construct global application.
    application = QtGui.QApplication('ftrack-connect')
    application.setOrganizationName('ftrack')
    application.setOrganizationDomain('ftrack.com')
    application.setQuitOnLastWindowClosed(False)

    # Enable ctrl+c to quit application when started from command line.
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Construct main connect window and apply theme.
    connectWindow = ftrack_connect.ui.application.Application(
        theme=namespace.theme
    )

    return application.exec_()


if __name__ == '__main__':
    raise SystemExit(
        main(sys.argv[1:])
    )
