from Acquisition import aq_inner

from zope import component
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
        online_members = []
        request = self.context.request
        context = aq_inner(self.context)
        get_online_users = \
            component.getMultiAdapter(
                                (context, request),
                                name="get_online_users"
                                )

        online_contacts = get_online_users()
        member = self.get_authenticated_member()
        if member.getId() in online_contacts:
            online_contacts.remove(member.getId())

        pm = getToolByName(self, 'portal_membership')
        members = pm.listMembers()
        for member in members:
            if member.getId() in online_contacts:
                online_members.append(member)
                
        return online_members


class AddForm(base.NullAddForm):
    """ """
    def create(self):
        return Assignment()


