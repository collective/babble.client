from zope import schema
from zope.formlib import form
from zope.interface import implements

from plone.portlets.interfaces import IPortletDataProvider
from plone.app.portlets.portlets import base

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.utils import getToolByName

from babble.client import utils
from babble.client import BabbleMessageFactory as _

class IChatRooms(IPortletDataProvider):
    """ Interface for a portlet showing the chat rooms available to the user.
    """
    header = schema.TextLine(
                        title=_(u"Portlet header"),
                        description=_(u"Title of the rendered portlet"),
                        default=_(u"Chat rooms available"),
                        required=True)


class Assignment(base.Assignment):
    """ This is what is actually managed through the portlets UI and associated
        with columns.
    """
    implements(IChatRooms)

    header = u""

    def __init__(self, header=_(u"Chat rooms")):
        self.header = header

    @property
    def title(self):
        """ This property is used to give the title of the portlet in the
            'manage portlets' screen. Here, we use the title that the user gave.
        """
        return self.header


class Renderer(base.Renderer):
    """
    This is registered in configure.zcml. The referenced page template is
    rendered, and the implicit variable 'view' will refer to an instance
    of this class. Other methods can be added and referenced in the template.
    """
    render = ViewPageTemplateFile('chatrooms.pt')

    def get_chat_rooms(self):
        return utils.get_chat_rooms(self.context)

    def get_id(self):
        """ """
        return 'available-chatrooms-portlet-%d' % self.__hash__()
        
    def title(self):
        return self.data.header

    def is_anonymous(self):
        """ """
        pm = getToolByName(self.context, 'portal_membership')
        return pm.isAnonymousUser()


class AddForm(base.AddForm):
    """ """
    form_fields = form.Fields(IChatRooms)
    label = _(u"Add an 'Chat Rooms' Portlet")
    description = _(
            u"This portlet displays the chat rooms available to the current "
            u"user and enables them to open and participate in them")

    def create(self, data):
        return Assignment(**data)


class EditForm(base.EditForm):
    """ """
    form_fields = form.Fields(IChatRooms)

    label = _(u"Edit 'Chat Rooms' Portlet")
    description = _(
            u"This portlet displays the chat rooms available to the current "
            u"user and enables them to open and participate in them")

