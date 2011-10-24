import cgi
import logging
import random
import socket
import xmlrpclib
import simplejson as json
from zope.interface import implements
from zope.component.hooks import getSite

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.Five.browser import BrowserView
from Products.CMFCore.utils import getToolByName

from babble.client.browser.interfaces import IChat
from babble.client.browser.interfaces import IChatBox
from babble.client import utils
from babble.client import BabbleException
from babble.client.config import SUCCESS
from babble.client.config import TIMEOUT
from babble.client.config import AUTH_FAIL
from babble.client.config import NULL_DATE

log = logging.getLogger('babble.client/browser/chat.py')

class BabbleView(BrowserView):
    """ Base view for common methods """

    def get_fullname(self, username):
        """ Get user via his ID and return his fullname
        """
        pm = getToolByName(self.context, 'portal_membership')
        member = pm.getMemberById(username)
        if not member:
            return username # Not sure what to do here...

        if not member.hasProperty('fullname'):
            return username
        return member.getProperty('fullname') or username


class Chat(BabbleView):
    implements(IChat)

    def initialize(self):
        """ Check if the user is registered, and register if not... 
        """
        pm = getToolByName(self.context, 'portal_membership')
        if pm.isAnonymousUser():
            return json.dumps({'status': AUTH_FAIL})

        member = pm.getAuthenticatedMember()
        username = member.getId()
        log.debug('initialize called, username: %s' % username)
        
        server = utils.getConnection(self.context)
        try:
            resp = json.loads(server.isRegistered(username))
        except socket.timeout:
            # Catch timeouts so that we can notify the caller
            log.error('initialize: timeout error for  %s' % username)
            # We return the same output as the poll would have
            # returned...
            return json.dumps({'status': TIMEOUT})

        if not resp['is_registered']:
            password = str(random.random())
            json.loads(server.register(username, password))
            setattr(member, 'chatpass', password)

        return json.dumps({'status': SUCCESS})


    def get_uncleared_messages(self, audience=None, mark_cleared=False):
        """ Retrieve the uncleared messages from the chat server 
        """
        pm = getToolByName(self.context, 'portal_membership')
        if pm.isAnonymousUser():
            return
        member = pm.getAuthenticatedMember()

        username = member.getId()
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

        server = utils.getConnection(self.context)
        try:
            # self, username, password, partner, chatrooms, clear
            resp = server.getUnclearedMessages(
                                    username, 
                                    password, 
                                    audience, 
                                    [],
                                    mark_cleared )
        except xmlrpclib.Fault, e:
            err_msg = e.faultString.strip('\n').split('\n')[-1]
            log.error('Error from chat.service: getUnclearedMessages: %s' % err_msg)
            raise BabbleException(err_msg)
        except socket.timeout:
            # Catch timeouts so that we can notify the caller
            log.error('get_uncleared__messages: timeout error for  %s' % username)
            return json.dumps({
                            'status': TIMEOUT, 
                            'last_msg_date': NULL_DATE,
                            'messages': {},
                            })

        json_dict = json.loads(resp)

        if json_dict['status'] != SUCCESS:
            raise BabbleException(
                        'getUnclearedMessages for %s failed. %s' \
                        % (username, json_dict.get('errmsg','')))

        # Add the message sender's fullname to the messages dict and return
        msg_dict = {} 
        for username, messages  in json_dict['messages'].items(): 
            fullname = self.get_fullname(username)
            msg_dict[username] = (fullname, messages)

        return json.dumps({
                'status': json_dict['status'], 
                'last_msg_date': json_dict['last_msg_date'],
                'messages': msg_dict,
                })


    def poll(self, username):
        """ Poll the chat server to retrieve new online users and chat
            messages
        """
        pm = getToolByName(self.context, 'portal_membership')
        member = pm.getMemberById(username)
        if not member or not hasattr(member, 'chatpass'):
            return 

        password = getattr(member, 'chatpass') 
        server = utils.getConnection(self.context)
        # pars: username, password
        try:
            server.confirmAsOnline(username)
            msgs = server.getNewMessages(username, password)
        except socket.timeout:
            # Catch timeouts so that we can notify the caller
            log.error('poll: timeout error for  %s' % username)
            return json.dumps({
                            'status': TIMEOUT, 
                            'last_msg_date': NULL_DATE,
                            'messages': {},
                            })
        except xmlrpclib.Fault, e:
            err_msg = e.faultString
            log.error('Error from chat.service: getNewMessages: %s' % err_msg)
            raise BabbleException(err_msg)

        json_dict = json.loads(msgs)
        # Add the message sender's fullname to the messages dict and return
        msg_dict = {} 
        for username, messages  in json_dict.get('messages', {}).items(): 
            fullname = self.get_fullname(username)
            msg_dict[username] = (fullname, messages)

        chatroom_msg_dict = {} 
        for username, messages  in json_dict.get('chatroom_messages', {}).items(): 
            fullname = self.get_fullname(username)
            chatroom_msg_dict[username] = (fullname, messages)

        return json.dumps({
                'status': json_dict['status'], 
                'last_msg_date': json_dict['last_msg_date'],
                'messages': msg_dict,
                'chatroom_messages': chatroom_msg_dict,
                })


    def send_message(self, to, message, chat_type):
        """ Send a chat message 
        """
        pm = getToolByName(self.context, 'portal_membership')
        if pm.isAnonymousUser():
            return

        server = utils.getConnection(self.context)
        member = pm.getAuthenticatedMember()
        if not hasattr(member, 'chatpass'):
            return 

        message = cgi.escape(message)
        message = utils.urlize(message, blank=True, auto_escape=False) 
        password = getattr(member, 'chatpass') 
        username = member.getId()
        log.debug(u'Chat message from %s sent to %s' % (username, to))
        server = utils.getConnection(self.context)

        if chat_type == 'chatroom':
            func = server.sendChatRoomMessage
        else:
            func = server.sendMessage

        try:
            resp = func(username, password, to, message)
        except xmlrpclib.Fault, e:
            log.error('Error from chat.service: sendMessage: %s' % e)
            raise BabbleException(e)

        json_dict = json.loads(resp)
        if json_dict['status'] != SUCCESS:
            raise BabbleException('sendMessage from %s to %s failed. %s' \
                                        % (username, to, json_dict))
        return json.dumps({
                'status': json_dict['status'], 
                'last_msg_date': json_dict['last_msg_date'],
                })


    def clear_messages(self, audience):
        """ Mark the messages with an audience (i.e user or chatroom) as 
            cleared. This means that they won't be loaded and displayed again 
            next time that chat box is opened.
        """
        return self.get_uncleared_messages(audience=audience, mark_cleared=True)

class ChatBox(BabbleView):
    """ """
    implements(IChatBox)
    template = ViewPageTemplateFile('templates/chatbox.pt')

    def get_box_title(self, chat_id):
        """ """
        if not '_' in chat_id:
            return chat_id

        chat_type, contact = chat_id.split('_', 1)
        if chat_type == 'chatbox':
            return self.get_fullname(contact)
        elif chat_type == 'chatroom':
            return getSite().unrestrictedTraverse(contact).Title()
        return contact

    def reverse_escape(self, html):
        return utils.reverse_escape(html)

    def render_chat_box(self, chat_id, box_id):
        """ """
        chat_type, audience = chat_id.split('_', 1)
        response = utils.get_last_conversation(
                                        self.context, 
                                        audience, 
                                        chat_type)
        if chat_type == 'chatroom':
            messages = response['chatroom_messages']
        else:
            messages = response['messages']
        return self.template(
                        messages=messages, 
                        audience=audience,
                        box_id=box_id, 
                        chat_type=chat_type,
                        chat_id=chat_id ,)

