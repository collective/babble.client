import logging
import xmlrpclib
import simplejson as json
from zope.interface import implements
from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from babble.client.browser.interfaces import IChat

log = logging.getLogger('babble.client/browser/chat.py')

class BabbleException(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)



class Chat:
    implements(IChat)

    def _getConnection(self):
        """ Returns a connection to the chat service """
        context = aq_inner(self.context)
        mtool = getToolByName(context, 'portal_chat')
        return mtool.getConnection()


    def _authenticated_member(self):
        """ Returns the currently logged in member object """
        context = aq_inner(self.context)
        pm = getToolByName(context, 'portal_membership')
        return pm.getAuthenticatedMember()


    def get_online_users(self):
        """ """
        server = self._getConnection()
        try:
            online_users = server.getOnlineUsers()
        except xmlrpclib.Fault, e:
            err_msg = e.faultString.strip('\n').split('\n')[-1]
            log.error('Error from chat.service: getOnlineUsers: %s' % err_msg)
            raise BabbleException(err_msg)

        log.info("online_users: %s" % str(online_users))
        return online_users


    def initialize(self, user, open_chats):
        """ Initializion by fetching all open chat sessions and their uncleared
            and unread chat messages
        """
        log.info('initialize called, user: %s' % user)
        open_chats = open_chats.split('|')
        for s in ['', user]:
            if s in open_chats:
                open_chats.remove(s)

        server = self._getConnection()
        messages = []
        for chat_buddy in open_chats:
            try:
                # username, sender, auto_register, read, clear, confirm_online
                messages = server.getUnclearedMessages(
                                    user, chat_buddy, True, True, False, True)

            except xmlrpclib.Fault, e:
                err_msg = e.faultString
                # .strip('\n').split('\n')[-1]  was returning " "
                # because I hadn't added the /chatservice tool to my instance
                log.error('Error from chat.service: getUnclearedMessages: %s' % err_msg)
                raise BabbleException(err_msg)

        return json.dumps({'username': user, 'items': messages,})


    def poll(self, user):
        """ Poll the chat server to retrieve new online users and chat
            messages
        """
        if not user:
            return

        server = self._getConnection()
        try:
            # pars: username, sender, register, read, confirm_online
            messages = server.getUnreadMessages(user, None, True, True, True)
        except xmlrpclib.Fault, e:
            err_msg = e.faultString.strip('\n').split('\n')[-1]
            log.error('Error from chat.service: getUnreadMessages: %s' % err_msg)
            raise BabbleException(err_msg)

        return json.dumps({'items': messages })


    def send_message(self, user, to, message):
        """ Send a chat message """
        log.info('Chat message %s sent to %s' % (message, to))
        server = self._getConnection()
        try:
            server.sendMessage(user, to, message, True) # register=True
        except xmlrpclib.Fault, e:
            err_msg = e.faultString.strip('\n').split('\n')[-1]
            log.error('Error from chat.service: sendMessage: %s' % err_msg)
            raise BabbleException(err_msg)


    def get_last_conversation(self, user, chat_buddy):
        """ Get all the uncleared messages between user and chat_buddy
        """
        log.info('get_last_conversation')
        server = self._getConnection()
        try:
            #pars: username, sender, auto_register, read, clear, confirm_online
            mlist = server.getUnclearedMessages(
                                user, chat_buddy, True, True, False, True)

        except xmlrpclib.Fault, e:
            err_msg = e.faultString.strip('\n').split('\n')[-1]
            log.error('Error from chat.service: clearMessages: %s' % err_msg)
            raise BabbleException(err_msg)

        messages = mlist and mlist[0]['messages'] or []
        return json.dumps({'messages': messages})


    def clear_messages(self, user, chat_buddy):
        """ Mark the messages in a chat contact's messagebox as cleared.
            This means that they won't be loaded and displayed again next time
            that chat box is opened.
        """
        log.info('clear messages sent to buddy: %s' % (chat_buddy))
        server = self._getConnection()
        try:
            # passed pars: (username, sender, auto_register, read, clear)
            server.getUnclearedMessages(user, chat_buddy, True, True, True)
        except xmlrpclib.Fault, e:
            err_msg = e.faultString.strip('\n').split('\n')[-1]
            log.error('Error from chat.service: clearMessages: %s' % err_msg)
            raise BabbleException(err_msg)
