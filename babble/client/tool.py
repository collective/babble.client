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
        {   'id':'chat_service_url', 
            'type': 'string', 
            'mode':'w',
            'label': _('Chat Service URL'),
         },
        {   'id':'poll_max', 
            'type': 'int', 
            'mode':'w',
            'label': _('Maximum polling interval (milliseconds)'),
        },
        {   'id':'poll_min', 
            'type': 'int', 
            'mode':'w',
            'label': _('Minimum polling interval (milliseconds)'),
        },
        )
    chat_service_url = 'http://admin:admin@localhost:8080/chatservice'
    poll_max = 20000 
    poll_min = 3000

    def __setstate__(self, state):
        """ connect to chat service if they are defined """
        SimpleItemWithProperties.__setstate__(self, state)
        self.getConnection()

    def getConnection(self):
        """ Return a connection to the chat service """
        url = self.getProperty('chat_service_url')
        if not hasattr(self, '_v_chat_service_url'):
            self._v_chat_service_url = url
            self._v_connection = xmlrpclib.Server(url, allow_none=1)

        elif self._v_chat_service_url != url:
            self._v_chat_service_url = url
            self._v_connection = xmlrpclib.Server(url, allow_none=1)

        elif not hasattr(self, '_v_connection'):
            self._v_chat_service_url = url
            self._v_connection = xmlrpclib.Server(url, allow_none=1)

        return self._v_connection

InitializeClass(MessageTool)

