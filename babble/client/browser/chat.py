import logging
import xmlrpclib
import simplejson as json
from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName

log = logging.getLogger('babble.client/browser/chat.py')

class Chat:

    def _getConnection(self):
        """ Return a connection to the chat service """
        context = aq_inner(self.context)
        mtool = getToolByName(context, 'portal_chat')
        return mtool.getConnection()

    def _authenticated_member(self):
        """ Return the currently logged in member object """
        context = aq_inner(self.context)
        pm = getToolByName(context, 'portal_membership')
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

    def poll(self, user):
        """ Polling to retrieve online users and chat messages """
        server = self._getConnection()
        try:
            messages = server.getUnreadMessages(user, None, True, True) 
        except xmlrpclib.Fault, e:
            err_msg = e.faultString.strip('\n').split('\n')[-1]
            log.error('Error from chat.service: getUnreadMessages: %s' % err_msg)
            raise err_msg 
                
        return json.dumps({'items': messages})

    def start_session(self, open_chats):
        """ """
        member = self._authenticated_member().getId()
        if member == None:
            return json.dumps({'username': '', 'items': []})

        log.info('start_session called, member: %s' % member)
        open_chats = open_chats.split('|')
        for s in ['', member]:
            if s in open_chats:
                open_chats.remove(s)

        server = self._getConnection()
        messages = []
        for user in open_chats:
            try:
                messages = \
                    server.getUnclearedMessages(member, user, True,  True, False) 
            except xmlrpclib.Fault, e:
                err_msg = e.faultString.strip('\n').split('\n')[-1]
                log.error('Error from chat.service: getUnclearedMessages: %s' % err_msg)
                raise err_msg 

        return json.dumps({'username': member, 'items': messages})

