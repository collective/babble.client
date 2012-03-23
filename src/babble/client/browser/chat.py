import sys
import cgi
import logging
import random
import socket
import xmlrpclib
import simplejson as json
import transaction
from zope.interface import implements
from zope.component.hooks import getSite

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.Five.browser import BrowserView
from Products.CMFCore.utils import getToolByName

from babble.client import config
from babble.client import iso8601
from babble.client import utils
from babble.client.browser.interfaces import IChat
from babble.client.browser.interfaces import IChatBox

log = logging.getLogger(__name__)

class Chat(BrowserView):
    implements(IChat)

    def initialize(self, username=None):
        """ Check if the user is registered, and register if not...
        """
        pm = getToolByName(self.context, 'portal_membership')
        if pm.isAnonymousUser():
            return json.dumps(config.AUTH_FAIL_RESPONSE)

        if username is None:
            member = pm.getAuthenticatedMember()
            username = member.getId()
        else:
            member = pm.getMemberById(username)

        log.debug('initialize called, username: %s' % username)
        server = utils.get_connection(self.context)
        if server is None:
            return json.dumps({'status': config.SERVER_ERROR})

        try:
            resp = json.loads(server.isRegistered(username))
        except socket.error, e:
            # Catch socket errors: timeouts connection refusede etc. 
            # so that we can notify the caller
            log.warn('Socket error for %s %s' % (username, e))
            # We return the same output as the poll would have
            # returned...
            return json.dumps({'status': config.TIMEOUT})
        except xmlrpclib.ProtocolError, e:
            # Handle errors such as Unauthorized
            log.warn('xmlrpclib.ProtocolError error for %s: %s %s' % (
                    username, e.errcode, e.errmsg))
            return json.dumps({'status': config.TIMEOUT})

        if not resp['is_registered']:
            password = str(random.random())
            json.loads(server.register(username, password))
            setattr(member, 'chatpass', password)
            # Commit this transaction so that the chatpass is not lost if
            # something fails after this step
            transaction.commit()

        return json.dumps({'status': config.SUCCESS})


    def get_uncleared_messages(self, audience='*', chatrooms='*', until=None, mark_cleared=False):
        """ Retrieve the uncleared messages from the chat server.

            If audience == '*', messages from all conversation partners are
            returned.
        """
        pm = getToolByName(self.context, 'portal_membership')
        if pm.isAnonymousUser():
            return json.dumps({'status': config.AUTH_FAIL})
        member = pm.getAuthenticatedMember()

        username = member.getId()
        if hasattr(member, 'chatpass'):
            password = getattr(member, 'chatpass')
        else:
            log.warn("The member %s is registered in the Chat Service, but "
            "doesn't have his password anymore. This could be because an "
            "existing Chat Service is being used with a new Plone instance. "
            "Deleting the user's entry in the Chat Service's acl_users and "
            "folder in 'users' should fix this problem" % username)
            # This will raise an attribute error
            password = getattr(member, 'chatpass')

        server = utils.get_connection(self.context)
        if server is None:
            return json.dumps({'status': config.SERVER_ERROR})
        try:
            # self, username, password, partner, chatrooms, clear
            resp = server.getUnclearedMessages(
                                    username,
                                    password,
                                    audience,
                                    chatrooms,
                                    until,
                                    mark_cleared )
        except xmlrpclib.Fault, e:
            err_msg = e.faultString.strip('\n').split('\n')[-1]
            log.warn('Error from chat.service: getUnclearedMessages: %s' % err_msg)
            return json.dumps({'status': config.SERVER_ERROR})
        except socket.timeout:
            # Catch timeouts so that we can notify the caller
            log.warn('get_uncleared__messages: timeout error for  %s' % username)
            return json.dumps({'status': config.TIMEOUT_RESPONSE})

        json_dict = json.loads(resp)
        return resp


    def poll(self, username, since):
        """ Poll the chat server to retrieve new online users and chat
            messages
        """
        if not isinstance(username, str) and not isinstance(username, unicode):
            return json.dumps({'status': config.AUTH_FAIL})

        context = self.context
        password = None
        cache = getattr(self, '_v_user_password_dict', {})
        password = getattr(cache, username.encode('utf-8'), None)
        if password is None:
            pm = getToolByName(context, 'portal_membership')
            member = pm.getMemberById(username)
            if not member or not hasattr(member, 'chatpass'):
                return json.dumps({'status': config.AUTH_FAIL})

            password = getattr(member, 'chatpass')
            cache[username.encode('utf-8')] = password

        server = utils.get_connection(context)
        if server is None:
            return json.dumps({'status': config.SERVER_ERROR})
        try:
            server.confirmAsOnline(username)
            return server.getNewMessages(username, password, since)
        except socket.timeout:
            # Catch timeouts so that we can notify the caller
            log.warn('poll: timeout error for  %s' % username)
            return json.dumps({'status': config.TIMEOUT_RESPONSE})
        except xmlrpclib.Fault, e:
            err_msg = e.faultString
            log.warn('Error from chat.service: getNewMessages: %s' % err_msg)
            return json.dumps({'status': config.SERVER_ERROR})
        except:
            log.warn("Unexpected error: %s", sys.exc_info()[0])
            return json.dumps({'status': config.SERVER_ERROR})


    def send_message(self, to, message, chat_type='chatbox'):
        """ Send a chat message
        """
        pm = getToolByName(self.context, 'portal_membership')
        if pm.isAnonymousUser():
            return json.dumps({'status': config.AUTH_FAIL})

        server = utils.get_connection(self.context)
        if server is None:
            return json.dumps({'status': config.SERVER_ERROR})
        member = pm.getAuthenticatedMember()
        if not hasattr(member, 'chatpass'):
            return json.dumps({'status': config.AUTH_FAIL})

        message = cgi.escape(message)
        message = utils.urlize(message, blank=True, auto_escape=False)
        password = getattr(member, 'chatpass')
        username = member.getId()
        fullname = member.getProperty('fullname') or username
        log.debug(u'Chat message from %s sent to %s' % (username, to))
        server = utils.get_connection(self.context)
        if server is None:
            return json.dumps({'status': config.SERVER_ERROR})

        if chat_type == 'chatroom':
            func = server.sendChatRoomMessage
        else:
            func = server.sendMessage
        try:
            resp = func(username, password, fullname, to, message)
        except xmlrpclib.Fault, e:
            log.warn('Error from chat.service: sendMessage: %s' % e)
            return json.dumps({'status': config.SERVER_ERROR})

        json_dict = json.loads(resp)
        return json.dumps({
                'status': json_dict['status'],
                'last_msg_date': json_dict.get('last_msg_date', config.NULL_DATE),
                })


    def clear_messages(self, audience, chat_type, until):
        """ Mark the messages with an audience (i.e user or chatroom) as
            cleared. This means that they won't be loaded and displayed again
            next time that chat box is opened.
        """
        if chat_type == 'chatroom':
            return self.get_uncleared_messages(
                                    chatrooms=audience,
                                    mark_cleared=True, 
                                    until=until)
        else:
            return self.get_uncleared_messages(
                                    audience=audience,
                                    mark_cleared=True, 
                                    until=until)


class ChatBox(BrowserView):
    """ """
    implements(IChatBox)
    template = ViewPageTemplateFile('templates/chatbox.pt')


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


    def _to_local_timezone(self, messages, tzoffset):
        tzoffset = iso8601.FixedOffset(0, int(tzoffset), '')
        for key in messages.keys():
            for mtuple in messages[key]:
                # Change message times to local timezone
                olddate = iso8601.parse_date(mtuple[2])
                date = (olddate + tzoffset.offset).replace(tzinfo=tzoffset)
                mtuple[2] = date.isoformat()
        return messages


    def render_chat_box(self, chat_id, box_id, tzoffset):
        """ """
        chat_type, audience = chat_id.split('_', 1)
        response = utils.get_last_conversation(
                                        self.context,
                                        audience,
                                        chat_type)

        if response['status'] == config.AUTH_FAIL:
            return
        elif response['status'] != config.SUCCESS:
            if response.get('errmsg'):
                log.warn(response['errmsg'])
            messages = {}
            return
        elif chat_type == 'chatroom':
            messages = response['chatroom_messages']
        else:
            messages = response['messages']

        messages = self._to_local_timezone(messages, tzoffset)
        return self.template(
                        messages=messages,
                        audience=audience,
                        last_msg_date=response['last_msg_date'],
                        box_id=box_id,
                        chat_type=chat_type,
                        chat_id=chat_id ,)

