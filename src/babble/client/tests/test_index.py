import transaction
from plone.dexterity.utils import createContentInContainer
from plone.uuid.interfaces import IUUID
from babble.client import index
from babble.client import utils
from babble.client.tests.base import TestCase

class TestIndex(TestCase):
    """ Tests the babble/client/browser/chat.py module
    """

    def test_index_registerd(self):
        """ """
        # Let's check that the index is in the catalog
        catalog = self.portal.portal_catalog
        self.assertTrue('participants' in catalog.indexes())

    def _getTargetClass(self):
        from Products.CMFCore.CatalogTool import IndexableObjectWrapper

        return IndexableObjectWrapper

    def test_index(self):
        portal = self.portal
        catalog = self.portal.portal_catalog

        # Add a chatroom
        chatroom = createContentInContainer(
                        portal, 
                        'babble.client.chatroom',
                        checkConstraints=False)

        # Check that one can query for it via participants
        ps = catalog(participants='portal_owner')
        self.assertEquals(len(ps), 1)
        self.assertTrue(IUUID(ps[0].getObject()), IUUID(chatroom))

        # Check the indexer manually
        indexed = index.participants(chatroom)()
        self.assertEquals(indexed, ['portal_owner'])

        # Add a new user
        self.create_user('user1', 'secret')

        # Give the user a local role on the chatroom
        chatroom.manage_addLocalRoles('user1', ('Reader',))

        # Check the indexer manually
        indexed = index.participants(chatroom)()
        self.assertEquals(indexed, ['user1', 'portal_owner'])

        # Recatalog the object and check if one can query for the new user.
        catalog.indexObject(chatroom)
        ps = catalog(participants='user1')
        self.assertEquals(len(ps), 1)
        self.assertTrue(IUUID(ps[0].getObject()), IUUID(chatroom))

        # Add another user
        self.create_user('user2', 'secret')

        # This time we don't give this user a local role on the chatroom

        # Check the indexer manually
        indexed = index.participants(chatroom)()
        self.assertEquals(indexed, ['user1', 'portal_owner'])

        # Recatalog the object and check if one can query for the new user.
        catalog.indexObject(chatroom)
        ps = catalog(participants='user2')
        self.assertEquals(len(ps), 0)

        catalog.unindexObject(chatroom)
        portal.manage_delObjects(['babble.client.chatroom'])
        transaction.commit()


    def test_utils(self):
        portal = self.portal
        catalog = self.portal.portal_catalog

        # Creat new use and log in
        self.create_user('user1', 'secret')
        self.login(name='user1')

        # Create some chatrooms (of which user1 will be owner) 
        for i in range(0, 3):
            chatroom = createContentInContainer(
                            portal, 
                            'babble.client.chatroom',
                            checkConstraints=False,
                            title='Chatroom %d' % i,
                            )

        rooms = utils.get_chat_rooms(portal)
        self.assertEquals(len(rooms), 3)

        # Create new user
        self.loginAsPortalOwner()
        self.create_user('user2', 'secret')
        self.login(name='user2')

        # This user doesn't have local roles so should not get the rooms
        rooms = utils.get_chat_rooms(portal)
        self.assertEquals(len(rooms), 0)

        # Even if this user is a site Administrators they should not
        self.loginAsPortalOwner()
        portal_groups = portal.portal_groups
        portal_groups.addPrincipalToGroup('user2', "Administrators")
        self.login(name='user2')

        rooms = utils.get_chat_rooms(portal)
        self.assertEquals(len(rooms), 0)

        # Check that they do if a local role is added.
        chatroom = portal['chatroom-1']
        chatroom.manage_addLocalRoles('user2', ('Reader',))
        chatroom.reindexObject()
        rooms = utils.get_chat_rooms(portal)
        self.assertEquals(len(rooms), 1)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestIndex))
    return suite



