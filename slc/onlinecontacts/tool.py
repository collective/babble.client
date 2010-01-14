import logging
import xmlrpclib

from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from Products.CMFCore.utils import UniqueObject
from Products.CMFCore.utils import SimpleItemWithProperties

log = logging.getLogger('babble.client/tool.py')

class MessageTool(UniqueObject, SimpleItemWithProperties):
    meta_type = 'Chat Tool'
    id = 'portal_chat'
    security = ClassSecurityInfo()
    _properties = (
        {'id':'title', 'type': 'string', 'mode':'w',
         'label':'Title'},
        {'id':'description', 'type': 'text', 'mode':'w',
         'label':'Description'},
        {'id':'chat_service_url', 'type': 'string', 'mode':'w',
         'label':'Chat Service URL'},
        )
    title = ''
    description = ''
    chat_service_url = 'http://admin:admin@localhost:8080/chatservice'

    def __setstate__(self, state):
        """ connect to chat service if they are defined """
        SimpleItemWithProperties.__setstate__(self, state)
        self.getConnection()

    def getConnection(self):
        """ Return a connection to the chat service """
        if not hasattr(self, '_v_connection'):
            url = self.getProperty('chat_service_url')
            self._v_connection = xmlrpclib.Server(url, allow_none=1)
        return self._v_connection


InitializeClass(MessageTool)
