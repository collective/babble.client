import simplejson as json

from zope.component import getMultiAdapter
from zope.component.interfaces import ObjectEvent
from zope.interface import Interface
from zope.interface import implements
from zope.lifecycleevent.interfaces import IObjectModifiedEvent

from zope.app.component.hooks import getSite

from five import grok

from Products.CMFCore.utils import getToolByName
from Products.PlonePAS.interfaces.events import IUserInitialLoginInEvent

from babble.client.utils import getConnection
from babble.client.interfaces import IBabbleClientLayer


class ILocalRolesModifiedEvent(IObjectModifiedEvent):
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
    password = getattr(member, 'chatpass')

    catalog = getToolByName(site, 'portal_catalog')
    chatrooms = catalog(portal_type='babble.client.chatroom',
                        allowedRolesAndUsers=username ) 

    s = getConnection(site)
    for c in chatrooms:
        chatroom = c.getObject()
        path = '/'.join(chatroom.getPhysicalPath())
        response = json.loads(s.addChatRoomParticipant(
                                    username,
                                    password,
                                    path,
                                    username ))

