import logging
import simplejson as json

from zope.component import getMultiAdapter
from zope.component.interfaces import IObjectEvent
from zope.component.interfaces import ObjectEvent
from zope.interface import Interface
from zope.interface import implements

from zope.app.component.hooks import getSite

from five import grok

from Products.CMFCore.utils import getToolByName
from Products.PlonePAS.interfaces.events import IUserInitialLoginInEvent

from babble.client.utils import getConnection
from babble.client.interfaces import IBabbleClientLayer

log = logging.getLogger(__name__)


class ILocalRolesModifiedEvent(IObjectEvent):
    """The local roles on an event have been modified via the @@sharing page
    """

class LocalRolesModifiedEvent(ObjectEvent):
    """ """
    implements(ILocalRolesModifiedEvent)


@grok.subscribe(Interface, IUserInitialLoginInEvent)
def registerUserForChatRooms(user, event):
    """ """
    if not IBabbleClientLayer.providedBy(user.REQUEST):
        return
        
    site = getSite()
    username = user.getId()

    # Register the user for the chatservice
    view = getMultiAdapter((site, site.REQUEST), name='babblechat')
    view.initialize()
    
    mtool = getToolByName(site, 'portal_membership')
    member = mtool.getMemberById(username)
    try:
        password = getattr(member, 'chatpass')
    except AttributeError, e:
        log.error(e)
        log.error("%s does not have property 'chatpass'.\n"
                  "This usually happens when you have deleted and recreated a "
                  "user in Plone, while the Babble ChatService user remains. "
                  "Delete the ChatService user as well and retry." % username)
        return

    catalog = getToolByName(site, 'portal_catalog')
    chatrooms = catalog(portal_type='babble.client.chatroom',
                        participants=username ) 

    s = getConnection(site)
    for c in chatrooms:
        chatroom = c.getObject()
        path = '/'.join(chatroom.getPhysicalPath())
        response = json.loads(s.addChatRoomParticipant(
                                    username,
                                    password,
                                    path,
                                    username ))

