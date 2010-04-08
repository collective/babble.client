from zope.interface import implements

from plone.portlets.interfaces import IPortletDataProvider
from plone.app.portlets.portlets import base

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from babble.client import utils

class IOnlineContacts(IPortletDataProvider):
    """A portlet

    It inherits from IPortletDataProvider because for this portlet, the
    data that is being rendered and the portlet assignment itself are the
    same.
    """

class Assignment(base.Assignment):
    """ 
    This is what is actually managed through the portlets UI and associated
    with columns.
    """

    implements(IOnlineContacts)

    def __init__(self):
        pass

    @property
    def title(self):
        """ """
        return "Online contacts"


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


class AddForm(base.NullAddForm):
    """ """

    def create(self):
        return Assignment()


