import logging
import random
import xmlrpclib
import simplejson as json
from zope.interface import implements

from AccessControl.unauthorized import Unauthorized

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.Five.browser import BrowserView
from Products.CMFCore.utils import getToolByName

from babble.client.browser.interfaces import IChat
from babble.client.browser.interfaces import IChatBox
from babble.client import utils
from babble.client import BabbleException

log = logging.getLogger('babble.client/browser/chat.py')

class Chat:
    implements(IChat)

    def get_online_users(self):
        """ """
        online_users = utils.get_online_members(self.context)
        log.info("online_users: %s" % str(online_users))
        return online_users


    def initialize(self, username, open_chats):
        """ Initializion by fetching all open chat sessions and their uncleared
            and unread chat messages
        """
        log.info('initialize called, username: %s' % username)
        if username == 'Anonymous User':
            return

        open_chats = open_chats.split('|')
        for s in ['', username]:
            if s in open_chats:
                open_chats.remove(s)

        server = utils.getConnection(self.context)
        messages = []
        for chat_buddy in open_chats:
            try:
                if not server.isRegistered(username):
                    pm = getToolByName(self.context, 'portal_membership')
                    member = pm.getAuthenticatedMember()
                    if member.getId() != username:
                        raise Unauthorized(
                            '%s tried to authenticate as a different user %s' \
                            % (member.getId(), username))

                    password = str(random.random())
                    member.manage_addProperty('chatpass', password, 'string')
                    server.register(username, password)

                # username, sender, read, clear, confirm_online
                messages = server.getUnclearedMessages(
                                    username, chat_buddy, True, False, True)

            except xmlrpclib.Fault, e:
                err_msg = e.faultString
                # .strip('\n').split('\n')[-1]  was returning " "
                # because I hadn't added the /chatservice tool to my instance
                log.error('Error from chat.service: getUnclearedMessages: %s' % err_msg)
                raise BabbleException(err_msg)

        return json.dumps({'username': username, 'items': messages,})


    def poll(self, username):
        """ Poll the chat server to retrieve new online users and chat
            messages
        """
        if not username:
            return

        server = utils.getConnection(self.context)
        try:
            # pars: username, sender, read, confirm_online
            messages = server.getUnreadMessages(username, None, True, True)
        except xmlrpclib.Fault, e:
            err_msg = e.faultString.strip('\n').split('\n')[-1]
            log.error('Error from chat.service: getUnreadMessages: %s' % err_msg)
            raise BabbleException(err_msg)

        return json.dumps({'items': messages })


    def send_message(self, username, to, message):
        """ Send a chat message """
        log.info('Chat message %s sent to %s' % (message, to))
        server = utils.getConnection(self.context)
        try:
            server.sendMessage(username, to, message, True) # register=True
        except xmlrpclib.Fault, e:
            err_msg = e.faultString.strip('\n').split('\n')[-1]
            log.error('Error from chat.service: sendMessage: %s' % err_msg)
            raise BabbleException(err_msg)


    def get_last_conversation(self, username, chat_buddy):
        """ Get all the uncleared messages between user and chat_buddy
        """
        log.info('get_last_conversation')
        messages = utils.get_last_conversation(self.context, username, chat_buddy)
        return json.dumps({'messages': messages})


    def clear_messages(self, username, chat_buddy):
        """ Mark the messages in a chat contact's messagebox as cleared.
            This means that they won't be loaded and displayed again next time
            that chat box is opened.
        """
        log.info('clear messages sent to buddy: %s' % (chat_buddy))
        server = utils.getConnection(self.context)
        try:
            # passed pars: (username, sender, read, clear)
            server.getUnclearedMessages(username, chat_buddy, True, True, True)
        except xmlrpclib.Fault, e:
            err_msg = e.faultString.strip('\n').split('\n')[-1]
            log.error('Error from chat.service: clearMessages: %s' % err_msg)
            raise BabbleException(err_msg)


class ChatBox(BrowserView):
    """ """
    implements(IChatBox)
    template = ViewPageTemplateFile('templates/chatbox.pt')

    def render_chat_box(self, box_id, username, title):
        """ """
        messages = utils.get_last_conversation(self.context, username, title)
        return self.template(messages=messages, box_id=box_id, title=title)


