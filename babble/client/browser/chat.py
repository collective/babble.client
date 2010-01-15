import logging
import xmlrpclib
import simplejson as json
from Products.CMFCore.utils import getToolByName

log = logging.getLogger('babble.client/browser/chat.py')

class Chat:

    def _getConnection(self):
        """ Return a connection to the chat service """
        mtool = getToolByName(self.context, 'portal_chat')
        return mtool.getConnection()

    def _authenticated_member(self):
        """ Return the currently logged in member object """
        pm = getToolByName(self, 'portal_membership')
        return pm.getAuthenticatedMember()

    def send_message(self, user, to, message):
        """ Send a chat message """
        log.info('Chat message %s sent to %s' % (message, to))
        server = self._getConnection()
        try:
            server.sendMessage(user, to, message, True) # register=True
        except xmlrpclib.Fault, e:
            err_msg = e.faultString.strip('\n').split('\n')[-1]
            log.error('Error from chat.service: send_message: %s' % err_msg)
            raise err_msg 
        return u''

    def poll(self, user):
        """ Polling to retrieve online users and chat messages """
        server = self._getConnection()
        try:
            messages = server.getAllMessages(user, True) # register=True
        except xmlrpclib.Fault, e:
            err_msg = e.faultString.strip('\n').split('\n')[-1]
            log.error('Error from chat.service: send_message: %s' % err_msg)
            raise err_msg 

        return json.dumps({'items': messages})

    def start_session(self):
        """ """
        log.info('start_session called')
        member = self._authenticated_member()

        server = self._getConnection()
        try:
            messages = server.getAllMessages(member.id, True) # register=True
        except xmlrpclib.Fault, e:
            err_msg = e.faultString.strip('\n').split('\n')[-1]
            log.error('Error from chat.service: send_message: %s' % err_msg)
            raise err_msg 

        return json.dumps({'username': member.id, 'items': messages})


