# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack
import ftrack_api

_shared_session = None

def get_shared_session():
    '''Return shared ftrack_api session.'''
    global _shared_session
    if not _shared_session:
        _shared_session = ftrack_api.Session()

    return _shared_session


def get_session():
    '''Return new ftrack_api session configure without plugins or events.'''
    # TODO: Once API is thread-safe, consider switching to a shared session.
    return ftrack_api.Session(plugin_paths=[], auto_connect_event_hub=False)
