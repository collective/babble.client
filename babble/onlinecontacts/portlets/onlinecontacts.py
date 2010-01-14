from zope.interface import implements

from plone.portlets.interfaces import IPortletDataProvider
from plone.app.portlets.portlets import base

from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

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
        return "Who's online?"


class Renderer(base.Renderer):
    """
    This is registered in configure.zcml. The referenced page template is
    rendered, and the implicit variable 'view' will refer to an instance
    of this class. Other methods can be added and referenced in the template.
    """
    render = ViewPageTemplateFile('onlinecontacts.pt')

    def get_id(self):
        """ """
        return 'online-contacts-portlet-%d' % self.__hash__()

    def get_authenticated_member(self):
        """ """
        pm = getToolByName(self, 'portal_membership')
        return pm.getAuthenticatedMember()
    
    def get_online_contacts(self):
        """ """
        # XXX: Restrict this to online contacts only
        member = self.get_authenticated_member()
        pm = getToolByName(self, 'portal_membership')
        members = pm.listMembers()
        if member in members:
            members.remove(member)
        return members


class AddForm(base.NullAddForm):
    """ """
    def create(self):
        return Assignment()


