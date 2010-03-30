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
from babble.client.config import SUCCESS

log = logging.getLogger('babble.client/browser/chat.py')

class Chat:
    implements(IChat)

    def get_online_users(self):
        """ """
        online_users = utils.get_online_members(self.context)
        log.info("online_users: %s" % str(online_users))
        return online_users


    def confirm_as_online(self):
        """ """
        pm = getToolByName(self.context, 'portal_membership')
        if pm.isAnonymousUser():
            return

        server = utils.getConnection(self.context)
        member = pm.getAuthenticatedMember()
        server.confirmAsOnline(member.getId())


    def initialize(self):
        """ Initializion by fetching all open chat sessions and their uncleared
            and unread chat messages
        """
        pm = getToolByName(self.context, 'portal_membership')
        if pm.isAnonymousUser():
            return

        server = utils.getConnection(self.context)
        messages = []
        member = pm.getAuthenticatedMember()
        username = member.getId()
        log.info('initialize called, username: %s' % username)

        resp = json.loads(server.isRegistered(username))
        if not resp['is_registered']:
            password = str(random.random())
            resp = json.loads(server.register(username, password))
            if resp['status'] == SUCCESS:
                if member.hasProperty('chatpass'):
                    member.manage_delProperties(ids=['chatpass'])
                member.manage_addProperty('chatpass', password, 'string')

        password = getattr(member, 'chatpass') 
        try:
            # username, password, sender, read, clear
            resp = server.getUnclearedMessages(username, password, None, True, False)

        except xmlrpclib.Fault, e:
            err_msg = e.faultString
            # .strip('\n').split('\n')[-1]  was returning " "
            # because I hadn't added the /chatservice tool to my instance
            log.error('Error from chat.service: getUnclearedMessages: %s' % err_msg)
            raise BabbleException(err_msg)

        resp = json.loads(resp)
        messages = resp['messages']
        return json.dumps({'username': username, 'messages': messages,})


    def poll(self):
        """ Poll the chat server to retrieve new online users and chat
            messages
        """
        pm = getToolByName(self.context, 'portal_membership')
        if pm.isAnonymousUser():
            return 

        member = pm.getAuthenticatedMember()
        if not member.hasProperty('chatpass'):
            return 

        password = getattr(member, 'chatpass') 
        username = member.getId()
        server = utils.getConnection(self.context)
        try:
            # pars: username, password, read
            return server.getUnreadMessages(username, password, True)
        except xmlrpclib.Fault, e:
            err_msg = e.faultString.strip('\n').split('\n')[-1]
            log.error('Error from chat.service: getUnreadMessages: %s' % err_msg)
            raise BabbleException(err_msg)


    def send_message(self, to, message):
        """ Send a chat message """
        pm = getToolByName(self.context, 'portal_membership')
        if pm.isAnonymousUser():
            return

        log.info('Chat message %s sent to %s' % (message, to))
        server = utils.getConnection(self.context)
        member = pm.getAuthenticatedMember()
        if not member.hasProperty('chatpass'):
            return 

        password = getattr(member, 'chatpass') 
        username = member.getId()
        server = utils.getConnection(self.context)
        try:
            resp = server.sendMessage(username, password, to, message)
        except xmlrpclib.Fault, e:
            err_msg = e.faultString.strip('\n').split('\n')[-1]
            log.error('Error from chat.service: sendMessage: %s' % err_msg)
            raise BabbleException(err_msg)

        resp = json.loads(resp)
        if resp['status'] != SUCCESS:
            raise BabbleException('sendMessage from %s to %s failed' \
                                                        % (username, to))


    def get_last_conversation(self, contact):
        """ Get all the uncleared messages between user and contact
        """
        log.info('get_last_conversation')
        messages = utils.get_last_conversation(self.context, contact)
        return json.dumps({'messages': messages})


    def clear_messages(self, contact):
        """ Mark the messages in a chat contact's messagebox as cleared.
            This means that they won't be loaded and displayed again next time
            that chat box is opened.
        """
        log.info('clear messages sent to buddy: %s' % (contact))
        server = utils.getConnection(self.context)

        pm = getToolByName(self.context, 'portal_membership')
        member = pm.getAuthenticatedMember()
        if not member.hasProperty('chatpass'):
            return 

        password = getattr(member, 'chatpass') 
        username = member.getId()
        try:
            # passed pars: (username, password, sender, read, clear)
            resp = server.getUnclearedMessages(
                                            username, 
                                            password, 
                                            contact, 
                                            True, 
                                            True)
        except xmlrpclib.Fault, e:
            err_msg = e.faultString.strip('\n').split('\n')[-1]
            log.error('Error from chat.service: clearMessages: %s' % err_msg)
            raise BabbleException(err_msg)

        resp = json.loads(resp)
        if resp['status'] != SUCCESS:
            raise BabbleException(
                    'getUnclearedMessages for %s failed' % username)


class ChatBox(BrowserView):
    """ """
    implements(IChatBox)
    template = ViewPageTemplateFile('templates/chatbox.pt')

    def render_chat_box(self, box_id, contact):
        """ """
        messages = utils.get_last_conversation(self.context, contact)
        return self.template(messages=messages, box_id=box_id, title=contact)


