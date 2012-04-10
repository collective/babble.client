import logging
import xmlrpclib
import socket
import simplejson as json
from five import grok
from z3c.form.interfaces import IDisplayForm
from zope import schema
from zope.app.container.interfaces import IObjectAddedEvent
from zope.app.container.interfaces import IObjectRemovedEvent
from zope.component import getMultiAdapter
from zope.component.hooks import getSite
from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from plone.directives import dexterity, form
from plone.indexer.decorator import indexer
from zExceptions import Unauthorized
from Products.CMFCore.utils import getToolByName
from babble.client import BabbleMessageFactory as _
from babble.client import config
from babble.client.events import ILocalRolesModifiedEvent
from babble.client.utils import get_connection
from babble.client.utils import get_html_formatted_messages
from babble.client.utils import get_participants

log = logging.getLogger(__name__)

class IChatRoom(form.Schema):
    """ A ChatRoom represents a multi-user conversation. Any logged in user who
        has the 'view' permission on a chat room may participate.
    """
    conversation = schema.Text(
            default=_(u'No conversation yet'),
            )
    form.omitted(u'conversation')
    form.no_omit(IDisplayForm, u'conversation')
    form.widget(conversation="plone.app.z3cform.wysiwyg.WysiwygFieldWidget")


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

    s = get_connection(chatroom)
    try:
        result = json.loads(s.createChatRoom(
                                    member.getId(), 
                                    password, 
                                    '/'.join(chatroom.getPhysicalPath()), 
                                    get_participants(chatroom),
                                    ))
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
    if not chatroom.REQUEST.get('controller_state') or \
            chatroom.REQUEST.controller_state.id == 'delete_confirmation':
        # The object is not yet removed, the user have been presented a
        # confirmation prompt.
        return
        
    getMultiAdapter((chatroom, chatroom.REQUEST), name='babblechat').initialize()
    pm = getToolByName(chatroom, 'portal_membership')
    member = pm.getAuthenticatedMember()
    password = _getChatPassword(member)
    if password is None:
        return

    s = get_connection(chatroom)
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
    elif result['status'] == config.NOT_FOUND:
        log.error("The chatroom '%s' was not found on the chat server and "
                "could not be deleted." % chatroom.Title())


def _editChatRoom(chatroom):
    pm = getToolByName(chatroom, 'portal_membership')
    member = pm.getAuthenticatedMember()
    password = _getChatPassword(member)
    if password is None:
        return
            
    chatroom_path = '/'.join(chatroom.getPhysicalPath())
    s = get_connection(chatroom)
    participants = get_participants(chatroom)
    try:
        resp = json.loads(
                    s.editChatRoom(
                            member.getId(), 
                            password, 
                            chatroom_path, 
                            participants,
                    ))
    except xmlrpclib.Fault, e:
        err_msg = e.faultString.strip('\n').split('\n')[-1]
        log.error('Error from babble.server: editChatRoom: %s' % err_msg)
        return 
    except socket.error, e:
        log.error('Error from babble.server: editChatRoom: %s' % e)
        return 

    if resp['status'] == config.NOT_FOUND:
        s.createChatRoom(
                    member.getId(), 
                    password, 
                    chatroom_path,
                    participants)


@grok.subscribe(IChatRoom, IObjectModifiedEvent)
def handleChatRoomEdited(chatroom, event):
    """ """
    _editChatRoom(chatroom)
        

@grok.subscribe(IChatRoom, ILocalRolesModifiedEvent)
def handleChatRoomLocalRolesModified(chatroom, event):
    """ """
    _editChatRoom(chatroom)
    chatroom.reindexObject()


@indexer(IChatRoom)
def conversation(obj):
    return obj.conversation


class ChatRoom(dexterity.Container):
    grok.implements(IChatRoom)

    def __init__(self, id=None, **kwargs):
        super(ChatRoom, self).__init__(id, **kwargs)
        self.cached_conversation = self.conversation

    @property
    def conversation(self):
        site = getSite()
        pm = getToolByName(site, 'portal_membership')
        if pm.isAnonymousUser():
            # XXX: What do we do when anonymous has sharing rights?
            return _("Please log in to view this conversation")

        # self doesn't have a full acquisition chain, so we use the brain from the
        # catalog
        catalog = getToolByName(site, 'portal_catalog')
        ps = catalog(
                    portal_type=self.portal_type, 
                    id=self.id,
                    creation_date=self.creation_date,
                    modification_date=self.modification_date)
        if len(ps) != 1:
            return _("CatalogError: Could not retrieve the conversation. Please "
                     "contact your site administrator.")

        brain = ps[0]
        member = pm.getAuthenticatedMember()
        username = member.getId()
        password = _getChatPassword(member)
        if password is None:
            return _("Error fetching the conversation. You do not have chat "
                     "password. Please contact your site administrator.")

        s = get_connection(site)
        try:
            response = json.loads(s.getMessages(
                                    username, 
                                    password, 
                                    None, 
                                    [brain.getPath()],
                                    None,
                                    None ))
        except xmlrpclib.Fault, e:
            log.error('Error from babble.server: getMessages: %s' % e)
            return self.cached_conversation

        except socket.error, e:
            log.error('Error from babble.server: getMessages: %s' % e)
            return self.cached_conversation

        messages = response.get('chatroom_messages', {}).get(brain.getPath(), [])
        self.cached_conversation = get_html_formatted_messages(username, messages)
        return self.cached_conversation

