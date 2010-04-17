from zope import schema
from zope.formlib import form
from zope.interface import implements

from plone.portlets.interfaces import IPortletDataProvider
from plone.app.portlets.portlets import base

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from babble.client import utils
from babble.client import BabbleMessageFactory as _

class IOnlineContacts(IPortletDataProvider):
    """ Interface for a portlet showing the currently online contacts
    """
    header = schema.TextLine(
                        title=_(u"Portlet header"),
                        description=_(u"Title of the rendered portlet"),
                        default=_(u"Who's online?"),
                        required=True)


class Assignment(base.Assignment):
    """ This is what is actually managed through the portlets UI and associated
        with columns.
    """
    implements(IOnlineContacts)

    header = u""

    def __init__(self, header=_(u"Online contacts")):
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
    render = ViewPageTemplateFile('onlinecontacts.pt')

    def get_online_members(self):
        return utils.get_online_members(self.context)

    def get_id(self):
        """ """
        return 'online-contacts-portlet-%d' % self.__hash__()
        
    def title(self):
        return self.data.header


class AddForm(base.AddForm):
    """ """
    form_fields = form.Fields(IOnlineContacts)
    label = _(u"Add an 'Online Contacts' Portlet")
    description = _(
            u"This portlet displays the currently online users, and "
            u"enables you to chat with them")

    def create(self, data):
        return Assignment(**data)


class EditForm(base.EditForm):
    """ """
    form_fields = form.Fields(IOnlineContacts)

    label = _(u"Edit 'Online Contacts' Portlet")
    description = _(
            u"This portlet displays the currently online users, and "
            u"enables you to chat with them")

