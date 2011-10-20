import logging
import xmlrpclib
import socket
import simplejson as json
from five import grok
from z3c.form.interfaces import IDisplayForm
from zope import schema
from zope.app.container.interfaces import IObjectAddedEvent
from zope.component import adapter
from plone.directives import dexterity, form
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


@adapter(IChatRoom, IObjectAddedEvent)
def handleChatRoomAdded(chatroom, event):
    """ Register the chatroom with the messaging service.
    """
    pm = getToolByName(chatroom, 'portal_membership')
    member = pm.getAuthenticatedMember()
    password = _getChatPassword(member)
    if password is None:
        return

    participants = [r[0] for r in chatroom.get_local_roles()]
    s = getConnection(chatroom)
    try:
        s.createChatRoom(member.getId(), password, chatroom.id, participants)
    except xmlrpclib.Fault, e:
        err_msg = e.faultString.strip('\n').split('\n')[-1]
        log.error('Error from babble.server: createChatRoom: %s' % err_msg)
        return 
    except socket.error, e:
        log.error('Error from babble.server: createChatRoom: %s' % e)
        return 


@adapter(IChatRoom, ILocalRolesModifiedEvent)
def handleChatRoomLocalRolesModified(chatroom, event):
    """ """
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
            

