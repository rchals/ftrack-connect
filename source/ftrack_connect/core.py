# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os
import signal

from PySide import QtGui, QtCore

from ftrack_connect.tabwidget import TabWidget
from ftrack_connect.widget.login import Login

APPLICATION_ROOT = os.path.dirname(
    os.path.realpath(__file__)
)

# RESOURCEPATH environment variable is set by py2app/py2exe applications.
RESOURCE_ROOT_PATH = os.path.join(
    os.environ.get(
        'RESOURCEPATH',
        APPLICATION_ROOT
    ),
    '..', '..', 'resource'
)


# Enable ctrl+c to quit application when started from command line.
signal.signal(signal.SIGINT, signal.SIG_DFL)


class ConnectError(Exception):
    '''Base ftrack connect error.'''
    pass


class ApplicationWindow(QtGui.QMainWindow):
    '''Main window class for ftrack connect.'''

    # Signal to be used when login fails.
    loginError = QtCore.Signal(object)

    def __init__(self, *args, **kwargs):
        '''Initialise the main application window.'''
        super(ApplicationWindow, self).__init__(*args, **kwargs)

        if not QtGui.QSystemTrayIcon.isSystemTrayAvailable():
            raise ConnectError('No system tray located.')

        QtGui.QApplication.setQuitOnLastWindowClosed(False)

        self.logoIcon = QtGui.QIcon(
            '{0}/logo.png'.format(RESOURCE_ROOT_PATH)
        )
        self._setupStyle()

        self.plugins = {}

        self._initialiseTray()

        self.setObjectName('ftrack-connect-window')
        self.setWindowTitle('ftrack connect')
        self.resize(350, 600)
        self.move(50, 50)

        self.setWindowIcon(self.logoIcon)

        self.loginWidget = None
        self.login()

    def login(self):
        '''Login using stored credentials or ask user for them.'''

        # Get settings from store.
        settings = QtCore.QSettings()
        server = settings.value('login/server', None)
        username = settings.value('login/username', None)
        apiKey = settings.value('login/apikey', None)

        # If missing any of the settings bring up login dialog.
        if None in (server, username, apiKey):
            self.showLoginWidget()
        else:
            # Show login screen on login error.
            self.loginError.connect(self.showLoginWidget)

            # Try to login.
            self.loginWithCredentials(server, username, apiKey)

    def showLoginWidget(self):
        '''Show the login widget.'''
        if self.loginWidget is None:
            self.loginWidget = Login()
            self.setCentralWidget(self.loginWidget)
            self.loginWidget.login.connect(self.loginWithCredentials)
            self.loginError.connect(self.loginWidget.loginError.emit)
            self.focus()

            # Set focus on the login widget to remove any focus from its child
            # widgets.
            self.loginWidget.setFocus()

    def loginWithCredentials(self, url, username, apiKey):
        '''Connect to *url* with *username* and *apiKey*.

        loginError will be emitted if this fails.

        '''
        os.environ['FTRACK_SERVER'] = url
        os.environ['LOGNAME'] = username
        os.environ['FTRACK_APIKEY'] = apiKey

        # Import ftrack module and catch any errors.
        try:
            import ftrack

            # Force update the url of the server in case it was already set.
            ftrack.xmlServer.__init__('{url}/client/'.format(url=url), False)

            # Force update topic hub since it will set the url on initialise.
            ftrack.TOPICS.__init__()

        except Exception as error:

            # Catch connection error since ftrack module will connect on load.
            if str(error).find('Unable to connect on') >= 0:
                self.loginError.emit(str(error))

            # Reraise the error.
            raise

        # Access ftrack to validate login details.
        try:
            ftrack.getUUID()
        except ftrack.FTrackError as error:
            self.loginError.emit(str(error))
        else:
            # Store login details in settings.
            settings = QtCore.QSettings()
            settings.setValue('login/server', url)
            settings.setValue('login/username', username)
            settings.setValue('login/apikey', apiKey)

            self.configureConnectAndDiscoverPlugins()

    def configureConnectAndDiscoverPlugins(self):
        '''Configure connect and load plugins.'''

        # Local import to avoid connection errors.
        import ftrack
        ftrack.setup()
        self.tabPanel = TabWidget()
        self.setCentralWidget(self.tabPanel)

        self._discoverPlugins()

        from ftrack_connect.topic_thread import TopicThread
        self.topicThread = TopicThread()
        self.topicThread.ftrackConnectEvent.connect(self._routeEvent)
        self.topicThread.start()

    def _initialiseTray(self):
        '''Initialise and add application icon to system tray.'''
        self.trayMenu = self._createTrayMenu()

        self.tray = QtGui.QSystemTrayIcon(self)

        self.tray.setContextMenu(
            self.trayMenu
        )

        self.tray.setIcon(self.logoIcon)
        self.tray.show()

    def _createTrayMenu(self):
        '''Return a menu for system tray.'''
        menu = QtGui.QMenu(self)

        quitAction = QtGui.QAction(
            'Quit connect', self,
            triggered=QtGui.qApp.quit
        )

        focusAction = QtGui.QAction(
            'Open connect', self,
            triggered=self.focus
        )

        styleAction = QtGui.QAction(
            'Change theme', self,
            triggered=self._changeTheme
        )
        menu.addAction(styleAction)

        menu.addAction(focusAction)
        menu.addSeparator()
        menu.addAction(quitAction)

        return menu

    def _discoverPlugins(self):
        '''Find and load tab plugins in search paths.'''
        #: TODO: Add discover functionality and search paths.

        # Add publisher as a plugin.
        from ftrack_connect.publisher.core import register
        register(self)

    def _routeEvent(self, eventData):
        '''Route websocket event to publisher plugin based on *eventData*.

        *eventData* should contain 'plugin' and 'action'. Will raise
        `ConnectError` if no plugin is found or if action is missing on plugin.

        '''
        pluginName = eventData.get('plugin')
        method = eventData.get('action')

        try:
            plugin = self.plugins[pluginName]
        except KeyError:
            raise ConnectError(
                'Plugin "{0}" not found.'.format(
                    pluginName
                )
            )

        try:
            method = getattr(plugin, method)
        except AttributeError:
            raise ConnectError(
                'Method "{0}" not found on "{1}" plugin({2}).'.format(
                    method, pluginName, plugin
                )
            )

        method(**eventData)

    def _onWidgetRequestFocus(self, widget):
        '''Switch tab to *widget* and bring application to front.'''
        self.tabPanel.setCurrentWidget(widget)
        self.focus()

    def _onWidgetRequestClose(self, widget):
        '''Hide application upon *widget* request.'''
        self.hide()

    def _changeTheme(self):
        '''Change active application theme.'''
        if not hasattr(self, '_theme'):
            self._theme = 'light'

        if self._theme == 'dark':
            self._theme = 'light'
        else:
            self._theme = 'dark'

        self._setupStyle(self._theme)

    def _setupStyle(self, theme='light'):
        '''Set up application style using *theme*.'''
        QtGui.QApplication.setStyle('cleanlooks')

        # Load font
        QtGui.QFontDatabase.addApplicationFont(
            '{0}/font/open_sans_regular.ttf'.format(RESOURCE_ROOT_PATH)
        )

        # Load stylesheet
        styleSheetString = open(
            '{0}/style_{1}.css'.format(RESOURCE_ROOT_PATH, theme), 'r'
        ).read()
        self.setStyleSheet(styleSheetString)

    def add(self, widget, name=None):
        '''Add *widget* as tab with *name*.

        If *name* is None the name will be collected from the widget.

        '''
        if name is None:
            name = widget.getName()

        self.tabPanel.addTab(
            widget, name
        )

        self.plugins[name.lower()] = widget

        widget.requestFocus.connect(self._onWidgetRequestFocus)
        widget.requestClose.connect(self._onWidgetRequestClose)

    def focus(self):
        '''Focus and bring the window to top.'''
        self.activateWindow()
        self.show()
        self.raise_()
