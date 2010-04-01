from zope.component import getUtility, getMultiAdapter

from plone.portlets.interfaces import IPortletType
from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import IPortletAssignment
from plone.portlets.interfaces import IPortletDataProvider
from plone.portlets.interfaces import IPortletRenderer

from OFS.Folder import Folder

from babble.client.portlets import onlinecontacts
from babble.client.tests.base import TestCase

class TestPortlet(TestCase):

    def afterSetUp(self):
        self.loginAsPortalOwner()
        view = self.app.unrestrictedTraverse('+/addChatService.html')
        view(add_input_name='chatservice', title='Chat Service', submit_add=1)
        self.app._setOb('temp_folder', Folder('temp_folder'))

    def test_portlet_type_registered(self):
        portlet = getUtility(
            IPortletType,
            name="babble.client.onlinecontacts")
        self.assertEquals(portlet.addview,
                          'babble.client.onlinecontacts')

    def test_interfaces(self):
        portlet = onlinecontacts.Assignment()
        self.failUnless(IPortletAssignment.providedBy(portlet))
        self.failUnless(IPortletDataProvider.providedBy(portlet.data))

    def test_obtain_renderer(self):
        context = self.folder
        request = self.folder.REQUEST
        view = self.folder.restrictedTraverse('@@plone')
        manager = getUtility(IPortletManager, name='plone.rightcolumn',
                             context=self.portal)

        # TODO: Pass any keyword arguments to the Assignment constructor
        assignment = onlinecontacts.Assignment()

        renderer = getMultiAdapter(
            (context, request, view, manager, assignment), IPortletRenderer)
        self.failUnless(isinstance(renderer, onlinecontacts.Renderer))


class TestRenderer(TestCase):

    def afterSetUp(self):
        self.loginAsPortalOwner()
        view = self.app.unrestrictedTraverse('+/addChatService.html')
        view(add_input_name='chatservice', title='Chat Service', submit_add=1)

        self.portal.portal_chat.manage_changeProperties(**{'use_local_service': True})

        # The 'temp_folder' is not created for some reason, so do it here...
        self.app._setOb('temp_folder', Folder('temp_folder'))

    def renderer(self, context=None, request=None, view=None, manager=None,
                 assignment=None):
        context = context or self.folder
        request = request or self.folder.REQUEST
        view = view or self.folder.restrictedTraverse('@@plone')
        manager = manager or getUtility(
            IPortletManager, name='plone.rightcolumn', context=self.portal)

        assignment = assignment or onlinecontacts.Assignment()
        return getMultiAdapter((context, request, view, manager, assignment),
                               IPortletRenderer)

    def test_render(self):
        r = self.renderer(context=self.portal,
                          assignment=onlinecontacts.Assignment())
        r = r.__of__(self.folder)
        r.update()
        output = r.render()
        # TODO: Test output


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestPortlet))
    suite.addTest(makeSuite(TestRenderer))
    return suite

