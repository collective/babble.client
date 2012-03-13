import httplib
import logging
import xmlrpclib

from zope.interface import implements
from zope.component.hooks import getSite

from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from Products.CMFCore.utils import UniqueObject
from Products.CMFCore.utils import SimpleItemWithProperties

from babble.client import BabbleMessageFactory as _
from interfaces import IBabbleChatTool

log = logging.getLogger('babble.client/tool.py')

class CustomHTTPConnection(httplib.HTTPConnection):
    """ Thats ugly, but it seems to be the only way to add short timeouts 
        for these xmlrpclib connections only.
    """ 
    def getfile(self):
        return self.response

    def getreply(self):
        response = self.getresponse()
        self.response = response
        return response.status, response.reason, response.msg


class QuickTimeoutTransport(xmlrpclib.Transport):
    """ """
    def make_connection(self, host):
        host, extra_headers, x509 = self.get_host_info(host)
        try:
            return CustomHTTPConnection(host, timeout=5)
        except TypeError:
            # Python 2.4, Plone 3.x:
            # TypeError: __init__() got an unexpected keyword argument 'timeout'
            return CustomHTTPConnection(host)


class BabbleChatTool(UniqueObject, SimpleItemWithProperties):
    implements(IBabbleChatTool)
    meta_type = 'Chat Tool'
    id = 'portal_chat'
    security = ClassSecurityInfo()
    toolicon = 'skins/plone_images/topic_icon.png'
    _properties = (
        {   'id':'service_name', 
            'type': 'string', 
            'mode':'w',
            'label': _('Service name:'),
         },
        {   'id':'use_local_service', 
            'type': 'boolean', 
            'mode':'w',
            'label': _('The chat service is on the same machine.'),
         },
        {   'id':'host', 
            'type': 'string', 
            'mode':'w',
            'label': _('Hostname or relative path (relative to Zope root):'),
            'description': _('Hostname or relative path (if on the same server):'),
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
    service_name = 'chatservice'
    username = 'admin'
    password = 'admin'
    poll_max = 20000 
    poll_min = 5000 

    def __setstate__(self, state):
        """ connect to chat service if they are defined """
        SimpleItemWithProperties.__setstate__(self, state)
        self.getConnection()

    def getConnection(self):
        """ Return a connection to the chat service """
        # If 'self' has no acquisition context, then we can't access
        # portal_url. I don't yet know why this happens :-/
        if self.use_local_service:
            site = getSite()
            if not site:
                log.warn("No Site present. ZMI?")
                return
            zope_root = site.unrestrictedTraverse('/')
            try:
                return zope_root.unrestrictedTraverse(self.service_name)
            except KeyError, e:
                log.warn("KeyError: %s" % e)
                return

        username = self.getProperty('username')
        password = self.getProperty('password')
        host = self.getProperty('host')
        port = self.getProperty('port')
        name = self.getProperty('service_name')
        url = 'http://%s:%s@%s:%s/%s' % (username, password, host, port, name)

        if not hasattr(self, '_v_chat_service_url') \
                or not hasattr(self, '_v_connection') \
                or self._v_chat_service_url != url:

            self._v_chat_service_url = url
            self._v_connection = xmlrpclib.Server(
                                            url, 
                                            transport=QuickTimeoutTransport(), 
                                            allow_none=1
                                            )

        return self._v_connection

InitializeClass(BabbleChatTool)
