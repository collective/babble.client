import logging
import random
import socket
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
from babble.client.config import TIMEOUT
from babble.client.config import AUTH_FAIL

log = logging.getLogger('babble.client/browser/chat.py')

class BabbleView(BrowserView):
    """ Base view for commong methods """

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
        log.info('initialize called, username: %s' % username)
        
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


    def get_uncleared_messages(self, sender=None, read=True, clear=False):
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
            # passed pars: (username, password, sender, read, clear)
            resp = server.getUnclearedMessages(
                                            username, 
                                            password, 
                                            sender, 
                                            read, 
                                            clear
                                            )
        except xmlrpclib.Fault, e:
            err_msg = e.faultString.strip('\n').split('\n')[-1]
            log.error('Error from chat.service: getUnclearedMessages: %s' % err_msg)
            raise BabbleException(err_msg)
        except socket.timeout:
            # Catch timeouts so that we can notify the caller
            log.error('get_uncleared__messages: timeout error for  %s' % username)
            return json.dumps({
                            'status': TIMEOUT, 
                            'messages': {},
                            })

        json_dict = json.loads(resp)

        if json_dict['status'] != SUCCESS:
            raise BabbleException(
                    'getUnclearedMessages for %s failed' % username)

        # Add the message sender's fullname to the messages dict and return
        msg_dict = {} 
        for username, messages  in json_dict['messages'].items(): 
            fullname = self.get_fullname(username)
            msg_dict[username] = (fullname, messages)

        return json.dumps({
                'status': json_dict['status'], 
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
        # pars: username, password, read
        try:
            server.confirmAsOnline(username)
            msgs = server.getUnreadMessages(username, password, True)
        except socket.timeout:
            # Catch timeouts so that we can notify the caller
            log.error('poll: timeout error for  %s' % username)
            return json.dumps({
                            'status': TIMEOUT, 
                            'messages': {},
                            })
        except xmlrpclib.Fault, e:
            err_msg = e.faultString
            log.error('Error from chat.service: getUnreadMessages: %s' % err_msg)
            raise BabbleException(err_msg)

        json_dict = json.loads(msgs)
        # Add the message sender's fullname to the messages dict and return
        msg_dict = {} 
        for username, messages  in json_dict['messages'].items(): 
            fullname = self.get_fullname(username)
            msg_dict[username] = (fullname, messages)

        return json.dumps({
                'status': json_dict['status'], 
                'messages': msg_dict,
                })


    def send_message(self, to, message):
        """ Send a chat message 
        """
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
        return self.get_uncleared_messages(
                                        sender=contact, 
                                        read=True, 
                                        clear=True
                                        )

class ChatBox(BabbleView):
    """ """
    implements(IChatBox)
    template = ViewPageTemplateFile('templates/chatbox.pt')

    def reverse_escape(self, html):
        return utils.reverse_escape(html)

    def render_chat_box(self, box_id, contact):
        """ """
        response = utils.get_last_conversation(self.context, contact)
        return self.template(messages=response['messages'], box_id=box_id, title=contact)


