import logging
import xmlrpclib

from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from Products.CMFCore.utils import UniqueObject
from Products.CMFCore.utils import SimpleItemWithProperties

from babble.client import BabbleMessageFactory as _

log = logging.getLogger('babble.client/tool.py')

class MessageTool(UniqueObject, SimpleItemWithProperties):
    meta_type = 'Chat Tool'
    id = 'portal_chat'
    security = ClassSecurityInfo()
    _properties = (
        {   'id':'use_local_service', 
            'type': 'boolean', 
            'mode':'w',
            'label': _('Bypass XMLRPC by using a local chatservice:'),
        },
        {   'id':'name', 
            'type': 'string', 
            'mode':'w',
            'label': _('Service name:'),
         },
        {   'id':'host', 
            'type': 'string', 
            'mode':'w',
            'label': _('Host: (When not using a local chatservice)'),
        },
        {   'id':'port', 
            'type': 'string', 
            'mode':'w',
            'label': _('Port: (When not using a local chatservice)'),
         },
        {   'id':'username', 
            'type': 'string', 
            'mode':'w',
            'label': _('Username: (When not using a local chatservice)'),
         },
        {   'id':'password', 
            'type': 'string', 
            'mode':'w',
            'label': _('Password: (When not using a local chatservice)'),
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
        if self.use_local_service:
            return self.portal_url.getPortalObject().aq_parent.chatservice

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

