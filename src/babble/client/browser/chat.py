import logging
import random
import xmlrpclib
import simplejson as json
from zope.interface import implements

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.Five.browser import BrowserView
from Products.CMFCore.utils import getToolByName

from babble.client.browser.interfaces import IChat
from babble.client.browser.interfaces import IChatBox
from babble.client import utils
from babble.client import BabbleException
from babble.client.config import SUCCESS

log = logging.getLogger('babble.client/browser/chat.py')

class Chat(BrowserView):
    implements(IChat)

    def confirm_as_online(self):
        """ Let the chat server know that the currently authenticated used is
            still online 
        """
        pm = getToolByName(self.context, 'portal_membership')
        if pm.isAnonymousUser():
            return

        server = utils.getConnection(self.context)
        member = pm.getAuthenticatedMember()
        return server.confirmAsOnline(member.getId())


    def initialize(self):
        """ Initialization by fetching all unread chat messages...
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
                setattr(member, 'chatpass', password)

        if hasattr(member, 'chatpass'):
            password = getattr(member, 'chatpass') 
        else:
            log.error("The member %s is registered in the Chat Service, but "
            "doesn't have his password anymore. This could be because an "
            "existing Chat Service is being used with a new Plone instance. "
            "Deleting the user's entry in the Chat Service's acl_users and "
            "folder in 'users' should fix this problem" % username)
            # This will raise an attribute error
            password = getattr(member, 'chatpass') 

        try:
            server.confirmAsOnline(username)
            # pars: username, password, read
            return server.getUnreadMessages(username, password, True)

        except xmlrpclib.Fault, e:
            err_msg = e.faultString
            # .strip('\n').split('\n')[-1]  was returning " "
            # because I hadn't added the /chatservice tool to my instance
            log.error('Error from chat.service: getUnclearedMessages: %s' % err_msg)
            raise BabbleException(err_msg)


    def poll(self):
        """ Poll the chat server to retrieve new online users and chat
            messages
        """
        pm = getToolByName(self.context, 'portal_membership')
        if pm.isAnonymousUser():
            return 

        member = pm.getAuthenticatedMember()
        if not hasattr(member, 'chatpass'):
            return 

        password = getattr(member, 'chatpass') 
        username = member.getId()
        server = utils.getConnection(self.context)
        try:
            # pars: username, password, read
            server.confirmAsOnline(username)
            msgs = server.getUnreadMessages(username, password, True)
            # if json.loads(msgs)['messages']:
            #     log.info('In poll() for %s, msgs: %s' % (username, str(msgs)))
            return msgs
        except xmlrpclib.Fault, e:
            err_msg = e.faultString.strip('\n').split('\n')[-1]
            log.error('Error from chat.service: getUnreadMessages: %s' % err_msg)
            raise BabbleException(err_msg)


    def send_message(self, to, message):
        """ Send a chat message """
        pm = getToolByName(self.context, 'portal_membership')
        if pm.isAnonymousUser():
            return

        server = utils.getConnection(self.context)
        member = pm.getAuthenticatedMember()
        if not hasattr(member, 'chatpass'):
            return 

        message = utils.urlize(message, blank=True, auto_escape=True) 
        password = getattr(member, 'chatpass') 
        username = member.getId()
        log.info(u'Chat message from %s sent to %s' % (username, to))
        server = utils.getConnection(self.context)
        try:
            resp = server.sendMessage(username, password, to, message)
        except xmlrpclib.Fault, e:
            err_msg = e.faultString.strip('\n').split('\n')[-1]
            log.error('Error from chat.service: sendMessage: %s' % err_msg)
            raise BabbleException(err_msg)

        if json.loads(resp)['status'] != SUCCESS:
            raise BabbleException('sendMessage from %s to %s failed' \
                                                        % (username, to))

        return resp


    def clear_messages(self, contact):
        """ Mark the messages in a chat contact's messagebox as cleared.
            This means that they won't be loaded and displayed again next time
            that chat box is opened.
        """
        pm = getToolByName(self.context, 'portal_membership')
        if pm.isAnonymousUser():
            return

        log.info('clear messages sent to buddy: %s' % (contact))
        server = utils.getConnection(self.context)

        member = pm.getAuthenticatedMember()
        if not hasattr(member, 'chatpass'):
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

        if json.loads(resp)['status'] != SUCCESS:
            raise BabbleException(
                    'getUnclearedMessages for %s failed' % username)

        return resp


class ChatBox(BrowserView):
    """ """
    implements(IChatBox)
    template = ViewPageTemplateFile('templates/chatbox.pt')

    def reverse_escape(self, html):
        return utils.reverse_escape(html)

    def render_chat_box(self, box_id, contact):
        """ """
        messages = utils.get_last_conversation(self.context, contact)
        return self.template(messages=messages, box_id=box_id, title=contact)


