import logging
import xmlrpclib
import socket
import simplejson as json
from five import grok
from z3c.form.interfaces import IDisplayForm
from zope import schema
from zope.app.container.interfaces import IObjectAddedEvent
from zope.app.container.interfaces import IObjectEditedEvent
from zope.app.container.interfaces import IObjectRemovedEvent
from zope.component import getMultiAdapter
from plone.directives import dexterity, form
from zExceptions import Unauthorized
from Products.CMFCore.utils import getToolByName
from babble.client import BabbleMessageFactory as _
from babble.client import config
from babble.client.events import ILocalRolesModifiedEvent
from babble.client.utils import getConnection

log = logging.getLogger(__name__)

class IChatRoom(form.Schema):
    """ """
    conversation = schema.Text(
            title=_(u'label_conversation', default=u'Conversation'),
            default=_(u'No conversation yet'),
            )
    form.omitted(u'conversation')
    form.no_omit(IDisplayForm, u'conversation')


def _getChatPassword(member):
    if hasattr(member, 'chatpass'):
        return  getattr(member, 'chatpass') 
    else:
        log.error("%s does not have prop 'chatpass'\n"
                "This should not happen!" % member.getId())


@grok.subscribe(IChatRoom, IObjectAddedEvent)
def handleChatRoomAdded(chatroom, event):
    """ Register the chatroom with the messaging service.
    """
    getMultiAdapter((chatroom, chatroom.REQUEST), name='babblechat').initialize()
    pm = getToolByName(chatroom, 'portal_membership')
    member = pm.getAuthenticatedMember()
    password = _getChatPassword(member)
    if password is None:
        return

    plone_utils = getToolByName(chatroom, 'plone_utils')
    roles = plone_utils.getInheritedLocalRoles(chatroom)
    participants = [r[0] for r in roles]
    participants += [r[0] for r in chatroom.get_local_roles()]
    s = getConnection(chatroom)
    try:
        result = json.loads(s.createChatRoom(
                                    member.getId(), 
                                    password, 
                                    '/'.join(chatroom.getPhysicalPath()), 
                                    participants)
                                    )
    except xmlrpclib.Fault, e:
        log.error('XMLRPC Error from babble.server: createChatRoom: %s' % e)
        return 
    except socket.error, e:
        log.error('Socket Error from babble.server: createChatRoom: %s' % e)
        return 

    if result['status'] == config.AUTH_FAIL:
        raise Unauthorized


@grok.subscribe(IChatRoom, IObjectRemovedEvent)
def handleChatRoomRemoved(chatroom, event):
    """ Inform the messaging service of chatroom deletion.
    """
    if chatroom.REQUEST.controller_state.id == 'delete_confirmation':
        # The object is not yet removed, the user have been presented a
        # confirmation prompt.
        return
        
    getMultiAdapter((chatroom, chatroom.REQUEST), name='babblechat').initialize()
    pm = getToolByName(chatroom, 'portal_membership')
    member = pm.getAuthenticatedMember()
    password = _getChatPassword(member)
    if password is None:
        return

    s = getConnection(chatroom)
    try:
        result = json.loads(s.removeChatRoom(
                                    member.getId(), 
                                    password, 
                                    '/'.join(chatroom.getPhysicalPath()), 
                                    ))
    except xmlrpclib.Fault, e:
        log.error('XMLRPC Error from babble.server: removeChatRoom: %s' % e)
        return 
    except socket.error, e:
        log.error('Socket Error from babble.server: removeChatRoom: %s' % e)
        return 

    if result['status'] == config.AUTH_FAIL:
        raise Unauthorized


def _editChatRoom(chatroom):
    participants = []
    pm = getToolByName(chatroom, 'portal_membership')
    member = pm.getAuthenticatedMember()
    password = _getChatPassword(member)
    if password is None:
        return

    participants = [r[0] for r in chatroom.get_local_roles()]
    s = getConnection(chatroom)
    try:
        resp = json.loads(s.editChatRoom(member.getId(), password, chatroom.id, participants))
    except xmlrpclib.Fault, e:
        err_msg = e.faultString.strip('\n').split('\n')[-1]
        log.error('Error from babble.server: editChatRoom: %s' % err_msg)
        return 
    except socket.error, e:
        log.error('Error from babble.server: editChatRoom: %s' % e)
        return 

    if resp['status'] == config.NOT_FOUND:
        s.createChatRoom(member.getId(), password, chatroom.id, participants)


@grok.subscribe(IChatRoom, IObjectEditedEvent)
def handleChatRoomEdited(chatroom, event):
    """ """
    _editChatRoom(chatroom)
        

@grok.subscribe(IChatRoom, ILocalRolesModifiedEvent)
def handleChatRoomLocalRolesModified(chatroom, event):
    """ """
    _editChatRoom(chatroom)


class ChatRoom(dexterity.Container):
    grok.implements(IChatRoom)

    @property
    def conversation(self):
        pm = getToolByName(self, 'portal_membership')
        if pm.isAnonymousUser():
            # XXX: What do we do when anonymous has sharing rights?
            return _("Please log in to view this conversation")

        member = pm.getAuthenticatedMember()
        username = member.getId()
        password = _getChatPassword(member)
        if password is None:
            return _("Error fetching the conversation. You do not have chat "
                     "password. Please contact your system administrator.")

        s = getConnection(self)
        try:
            resp = s.getMessages(username, password, '*', [self.id])
        except xmlrpclib.Fault, e:
            err_msg = e.faultString.strip('\n').split('\n')[-1]
            log.error('Error from babble.server: getMessages: %s' % err_msg)
            return self.conversation
        except socket.error, e:
            log.error('Error from babble.server: getMessages: %s' % e)
            return self.conversation

        self.conversation = resp
        return self.conversation
            

