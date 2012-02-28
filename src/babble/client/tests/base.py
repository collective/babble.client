from zope import component
from zope.interface import alsoProvides

from OFS.Folder import Folder

from Products.Five import zcml
from Products.Five import fiveconfigure

from plone import browserlayer

from Products.Archetypes.Schema.factory import instanceSchemaFactory
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase import layer 

from babble.client.interfaces import IBabbleClientLayer

SiteLayer = layer.PloneSite

class BabbleClientLayer(SiteLayer):

    @classmethod
    def setUp(cls):
        """ Set up the additional products required
        """
        PRODUCTS = [
                'babble.server',
                'babble.client',
                ]
        ptc.setupPloneSite(products=PRODUCTS)

        fiveconfigure.debug_mode = True
        import babble.server
        zcml.load_config('configure.zcml', babble.server)
        import babble.client
        zcml.load_config('configure.zcml', babble.client)
        fiveconfigure.debug_mode = False
        
        browserlayer.utils.register_layer(IBabbleClientLayer, name='babble.client')

        component.provideAdapter(instanceSchemaFactory)
        SiteLayer.setUp()
    

class TestCase(ptc.PloneTestCase):
    """Base class used for test cases
    """
    layer = BabbleClientLayer

    def create_user(self, username, password, roles=['member'], domains=[]):
        uf = self.folder.acl_users
        uf.userFolderAddUser(username, password, roles, domains)
        self.mtool.createMemberarea(username)
        member = self.mtool.getMemberById(username)
        member.setMemberProperties({'fullname': username.split('@')[0].capitalize(),
                                    'email': '%s@example.com' % username, })

    def afterSetUp(self):
        self.loginAsPortalOwner()
        view = self.app.unrestrictedTraverse('+/addChatService.html')
        view(add_input_name='chatservice', title='Chat Service', submit_add=1)
        self.portal.portal_chat.use_local_service = True

        # The 'temp_folder' is not created for some reason, so do it here...
        self.app._setOb('temp_folder', Folder('temp_folder'))

        self.mtool = self.portal.portal_membership
        self.create_user('member1', 'secret')
        self.create_user('member2', 'secret')

        # Merely registering babble.client's browserlayer doesn't set it on the
        # request. This happens during IBeforeTraverseEvent, so we have to do 
        # it here manually
        alsoProvides(self.portal.REQUEST, IBabbleClientLayer)

