import datetime
import simplejson as json
from OFS.Folder import Folder
from babble.client import utils
from babble.client.tests.base import TestCase
from babble.client import BabbleException
from babble.server.config import SUCCESS

class TestChat(TestCase):
    """ Tests the babble/client/browser/chat.py module
    """

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


    def create_user(self, username, password, roles=['member'], domains=[]):
        uf = self.folder.acl_users
        uf.userFolderAddUser(username, password, roles, domains)
        self.mtool.createMemberarea(username)
        member = self.mtool.getMemberById(username)
        member.setMemberProperties({'fullname': username.capitalize(),
                                    'email': 'test@example.com', })

    def test_online_users(self):
        """ Tests the confirm_as_online and get_online_usernames methods
        """
        portal = self.portal
        traverse = portal.restrictedTraverse
    
        online_users = utils.get_online_usernames(portal)
        self.assertEquals(online_users, [])

        self.logout()
        resp = traverse('@@babblechat/confirm_as_online')()
        self.assertEquals(resp, None)

        self.login(name='member1')

        resp = traverse('@@babblechat/confirm_as_online')()
        resp = json.loads(resp)
        self.assertEquals(resp['status'], SUCCESS)

        online_users = utils.get_online_usernames(portal)
        self.assertEquals(online_users, ['member1'])

        self.login(name='member2')

        resp = traverse('@@babblechat/confirm_as_online')()
        resp = json.loads(resp)
        self.assertEquals(resp['status'], SUCCESS)

        online_users = utils.get_online_usernames(portal)
        self.assertEquals(online_users, ['member1', 'member2'])


    def test_messaging(self):
        """ Tests the initialization method
        """
        portal = self.portal
        traverse = portal.restrictedTraverse

        # Make sure member1 is registered on the chatserver by calling
        # initialize
        self.login(name='member1')
        resp = traverse('@@babblechat/initialize')()
        resp = json.loads(resp)
        self.assertEquals(resp['status'], SUCCESS)
        self.assertEquals(resp['messages'], {})

        
        # Test some methods' handling of anon users
        self.logout()
        resp = traverse('@@babblechat/initialize')()
        self.assertEquals(resp, None)
        resp = traverse('@@babblechat/poll')()
        self.assertEquals(resp, None)
        resp = traverse('@@babblechat/send_message')('member1', 'message')
        self.assertEquals(resp, None)
        resp = traverse('@@babblechat/clear_messages')('member1')
        self.assertEquals(resp, None)
        messages = utils.get_last_conversation(portal, 'member1')
        self.assertEquals(messages, {})

        # Test methods' response to a user ('portal_owner') who wasn't
        # initialized
        self.logout()
        self.loginAsPortalOwner()
        resp = traverse('@@babblechat/poll')()
        self.assertEquals(resp, None)
        resp = traverse('@@babblechat/send_message')('member1', 'message')
        self.assertEquals(resp, None)
        resp = traverse('@@babblechat/clear_messages')('member1')
        self.assertEquals(resp, None)
        messages = utils.get_last_conversation(portal, 'member1')
        self.assertEquals(messages, {})
        
        # Make sure member2 is registered on the chatserver by calling
        # initialize
        self.login(name='member2')
        resp = traverse('@@babblechat/initialize')()
        resp = json.loads(resp)
        self.assertEquals(resp['status'], SUCCESS)
        self.assertEquals(resp['messages'], {})

        # Send a message from member2 to member1 and note the time so that we
        # can test for it later on
        timeminutes = datetime.datetime.now().strftime("%H:%M")
        resp = traverse('@@babblechat/send_message')('member1', 'hello')
        resp = json.loads(resp)
        self.assertEquals(resp['status'], SUCCESS)

        # Poll for member1 and see if we got our message
        self.login(name='member1')
        resp = traverse('@@babblechat/poll')()
        resp = json.loads(resp)
        self.assertEquals(resp['status'], SUCCESS)

        # Check that a message was received from member2
        messages = resp['messages']
        self.assertEquals(messages.keys(), ['member2'])

        # Check the message format
        date = datetime.date.today().strftime("%Y/%m/%d")
        hello_message = ['member2', date, timeminutes, 'hello']
        self.assertEquals(
                messages['member2'], 
                [hello_message])

        # Check that the next poll returns no new messages
        resp = traverse('@@babblechat/poll')()
        resp = json.loads(resp)
        self.assertEquals(resp['status'], SUCCESS)
        self.assertEquals(resp['messages'], {})

        # Check that calling initialize again will return the original message,
        # since it hasn't been cleared yet
        resp = traverse('@@babblechat/initialize')()
        resp = json.loads(resp)
        self.assertEquals(resp['status'], SUCCESS)
        messages = resp['messages']
        self.assertEquals(messages.keys(), ['member2'])
        self.assertEquals(messages['member2'], [hello_message])

        # Also test that utils' get_last_conversation returns this message
        messages = utils.get_last_conversation(portal, 'member2')
        self.assertEquals(messages.keys(), ['member2'])
        self.assertEquals(messages['member2'], [hello_message])

        resp = traverse('@@babblechat/clear_messages')('member2')
        resp = json.loads(resp)
        self.assertEquals(resp['status'], SUCCESS)

        messages = utils.get_last_conversation(portal, 'member2')
        self.assertEquals(messages, {})

        resp = traverse('@@babblechat/initialize')()
        resp = json.loads(resp)
        self.assertEquals(resp['status'], SUCCESS)
        self.assertEquals(resp['messages'], {})

        # Test method's response to wrong authentication
        member = self.mtool.getAuthenticatedMember()
        member.chatpass = 'wrongpass'

        method = traverse('@@babblechat/send_message')
        pars = ['member2', 'message']
        self.assertRaises(BabbleException, method, *pars)

        method = traverse('@@babblechat/clear_messages')
        pars = ['member2']
        self.assertRaises(BabbleException, method, *pars)


    def test_render_chat_box(self):
        """ """
        self.login(name='member1')
        traverse = self.portal.restrictedTraverse
        resp = traverse('@@render_chat_box')('member1', 'member1')
        self.assertEquals(type(resp), unicode)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestChat))
    return suite

