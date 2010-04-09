import logging
import xmlrpclib

from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from Products.CMFCore.utils import UniqueObject
from Products.CMFCore.utils import SimpleItemWithProperties
from Products.CMFCore.utils import getToolByName

from babble.client import BabbleMessageFactory as _

log = logging.getLogger('babble.client/tool.py')

class MessageTool(UniqueObject, SimpleItemWithProperties):
    meta_type = 'Chat Tool'
    id = 'portal_chat'
    security = ClassSecurityInfo()
    _properties = (
        {   'id':'name', 
            'type': 'string', 
            'mode':'w',
            'label': _('Service name:'),
         },
        {   'id':'host', 
            'type': 'string', 
            'mode':'w',
            'label': _('Host:'),
        },
        {   'id':'port', 
            'type': 'string', 
            'mode':'w',
            'label': _('Port:'),
         },
        {   'id':'username', 
            'type': 'string', 
            'mode':'w',
            'label': _('Username:'),
         },
        {   'id':'password', 
            'type': 'string', 
            'mode':'w',
            'label': _('Password:'),
         },
        {   'id':'poll_max', 
            'type': 'int', 
            'mode':'w',
            'label': _('Maximum polling interval: (milliseconds)'),
        },
        {   'id':'poll_min', 
            'type': 'int', 
            'mode':'w',
            'label': _('Minimum polling interval: (milliseconds)'),
        },)

    use_local_service = False
    host = 'localhost'
    port = '8080'
    name = 'chatservice'
    username = 'admin'
    password = 'admin'
    poll_max = 20000 
    poll_min = 3000

    def __setstate__(self, state):
        """ connect to chat service if they are defined """
        SimpleItemWithProperties.__setstate__(self, state)
        self.getConnection()

    def getConnection(self):
        """ Return a connection to the chat service """
        # If 'self' has no acquisition context, then we can't access
        # portal_url. I don't yet know why this happens :-/
        if self.use_local_service and getToolByName(self, 'portal_url', None):
            zope_root = self.portal_url.getPortalObject().aq_parent
            if hasattr(zope_root, self.name):
                return zope_root[self.name]
            else:
                log.error("No Chat Service '%s' in the Zope root" % self.name)
                # This will raise KeyError 
                return zope_root[self.name]

        username = self.getProperty('username')
        password = self.getProperty('password')
        host = self.getProperty('host')
        port = self.getProperty('port')
        name = self.getProperty('name')
        url = 'http://%s:%s@%s:%s/%s' % (username, password, host, port, name)

        if not hasattr(self, '_v_chat_service_url') \
                or not hasattr(self, '_v_connection') \
                or self._v_chat_service_url != url:

            self._v_chat_service_url = url
            self._v_connection = xmlrpclib.Server(url, allow_none=1)

        return self._v_connection


InitializeClass(MessageTool)

