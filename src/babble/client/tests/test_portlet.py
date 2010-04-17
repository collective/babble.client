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
        self.portal.portal_chat.use_local_service = True

        # The 'temp_folder' is not created for some reason, so do it here...
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

    def test_add_form(self):
        portlet = getUtility(IPortletType, name="babble.client.onlinecontacts")
        mapping = self.portal.restrictedTraverse(
                                    '++contextportlets++plone.leftcolumn'
                                    )
        addview = mapping.restrictedTraverse('+/' + portlet.addview)
        assignment = addview.create({'header':u"Who is online?"})
        self.assertEquals(type(assignment), type(onlinecontacts.Assignment()))
        self.assertEquals(assignment.title, u"Who is online?")

    def test_obtain_renderer(self):
        context = self.folder
        request = self.folder.REQUEST
        view = self.folder.restrictedTraverse('@@plone')
        manager = getUtility(IPortletManager, name='plone.rightcolumn',
                             context=self.portal)

        assignment = onlinecontacts.Assignment()

        renderer = getMultiAdapter(
            (context, request, view, manager, assignment), IPortletRenderer)
        self.failUnless(isinstance(renderer, onlinecontacts.Renderer))

    def test_render(self):
        """ """
        context = self.portal
        assignment = onlinecontacts.Assignment()
        request = self.folder.REQUEST
        view = self.folder.restrictedTraverse('@@plone')
        manager = getUtility(
                IPortletManager, 
                name='plone.rightcolumn', 
                context=self.portal
                )

        renderer = getMultiAdapter(
                            (context, request, view, manager, assignment),
                            IPortletRenderer
                            )

        r = renderer.__of__(self.folder)
        r.update()
        output = r.render()
        self.assertEquals(type(output),unicode)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestPortlet))
    return suite

