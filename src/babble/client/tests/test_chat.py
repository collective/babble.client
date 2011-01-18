import datetime
from pytz import utc
import simplejson as json
from OFS.Folder import Folder
from Products.CMFCore.utils import getToolByName
from babble.client import utils
from babble.client.tests.base import TestCase
from babble.client import BabbleException
from babble.server import config 

class TestChat(TestCase):
    """ Tests the babble/client/browser/chat.py module
    """

    # TODO: Add tests for URL detection in messages... 

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
        """ Tests the confirm_as_online, get_online_usernames and 
            get_online_members methods
        """
        portal = self.portal
        traverse = portal.restrictedTraverse
    
        online_users = utils.get_online_usernames(portal)
        self.assertEquals(online_users, [])

        online_members = utils.get_online_members(portal)
        self.assertEquals(online_members, [])

        self.logout()
        member = self.mtool.getAuthenticatedMember()
        username = member.getId()
        server = utils.getConnection(self.portal)
        resp = json.loads(server.confirmAsOnline(username))
        self.assertEquals(resp['status'], config.AUTH_FAIL)

        self.login(name='member1')

        # resp = traverse('@@babblechat/confirm_as_online')()
        server = utils.getConnection(self.portal)
        resp = json.loads(server.confirmAsOnline('member1'))
        self.assertEquals(resp['status'], config.SUCCESS)

        online_users = utils.get_online_usernames(portal)
        self.assertEquals(online_users, ['member1'])

        # get_online_members ignores the currently logged in user.
        # So, if member1 is currently logged in and also online (according to
        # get_online_users), get_online_members will still return an empty
        # list.
        online_members = utils.get_online_members(portal)
        self.assertEquals(online_members, [])

        self.login(name='member2')

        server = utils.getConnection(self.portal)
        resp = json.loads(server.confirmAsOnline('member2'))
        self.assertEquals(resp['status'], config.SUCCESS)

        online_users = utils.get_online_usernames(portal)
        self.assertEquals(online_users, ['member1', 'member2'])

        # Again, the logged in member2 is ignored
        tm = getToolByName(portal, 'portal_membership')
        member1 = tm.getMemberById('member1')
        online_members = utils.get_online_members(portal)
        self.assertEquals(online_members, [member1])

        # Now the logged in member1 is ignored
        self.login(name='member1')
        member2 = tm.getMemberById('member2')
        online_members = utils.get_online_members(portal)
        self.assertEquals(online_members, [member2])


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
        self.assertEquals(resp['status'], config.SUCCESS)
        
        # Test some methods' handling of anon users
        self.logout()
        resp = traverse('@@babblechat/initialize')()
        self.assertEquals(resp, None)
        member = self.mtool.getAuthenticatedMember()
        resp = traverse('@@babblechat/poll')(member.getId())
        self.assertEquals(resp, None)
        resp = traverse('@@babblechat/send_message')('member1', 'message')
        self.assertEquals(resp, None)
        resp = traverse('@@babblechat/clear_messages')('member1')
        self.assertEquals(resp, None)
        messages = utils.get_last_conversation(portal, 'member1')
        self.assertEquals(messages['status'], config.AUTH_FAIL)
        self.assertEquals(messages['messages'], {})

        # Test methods' response to a user ('portal_owner') who wasn't
        # initialized
        self.logout()
        self.loginAsPortalOwner()

        member = self.mtool.getAuthenticatedMember()
        resp = traverse('@@babblechat/poll')(member.getId())
        self.assertEquals(resp, None)
        resp = traverse('@@babblechat/send_message')('member1', 'message')
        self.assertEquals(resp, None)

        method = traverse('@@babblechat/clear_messages')
        pars = ['member1']
        self.assertRaises(AttributeError, method, *pars)

        messages = utils.get_last_conversation(portal, 'member1')
        self.assertEquals(messages['status'], config.SERVER_FAULT)
        self.assertEquals(messages['messages'], {})
        
        # Make sure member2 is registered on the chatserver by calling
        # initialize
        self.login(name='member2')
        resp = traverse('@@babblechat/initialize')()
        resp = json.loads(resp)
        self.assertEquals(resp['status'], config.SUCCESS)

        # Send a message from member2 to member1 and note the time so that we
        # can test for it later on
        timeminutes = datetime.datetime.now(utc).strftime("%H:%M")
        resp = traverse('@@babblechat/send_message')('member1', 'hello')
        resp = json.loads(resp)
        self.assertEquals(resp['status'], config.SUCCESS)

        # Poll for member1 and see if we got our message
        self.login(name='member1')
        resp = traverse('@@babblechat/poll')('member1')
        resp = json.loads(resp)
        self.assertEquals(resp['status'], config.SUCCESS)

        # Check that a message was received from member2
        self.assertEquals(resp['messages'].keys(), ['member2'])

        # Check the message format
        date = datetime.date.today().strftime("%Y/%m/%d")
        hello_message = ['member2', date, timeminutes, 'hello']
        self.assertEquals(resp['messages']['member2'][0], 'Member2')
        self.assertEquals(resp['messages']['member2'][1], [hello_message])

        # Check that the next poll returns no new messages
        resp = traverse('@@babblechat/poll')('member1')
        resp = json.loads(resp)
        self.assertEquals(resp['status'], config.SUCCESS)
        self.assertEquals(resp['messages'], {})

        # Check that calling get_uncleared_messages will return the original message,
        # since it has not been cleared
        resp = traverse('@@babblechat/get_uncleared_messages')()
        resp = json.loads(resp)
        messages = resp['messages']
        self.assertEquals(resp['status'], config.SUCCESS)
        self.assertEquals(messages['member2'][0], 'Member2')
        self.assertEquals(messages['member2'][1], [hello_message])

        # Also test that utils' get_last_conversation returns this message
        messages = utils.get_last_conversation(portal, 'member2')
        self.assertEquals(messages.keys(), ['status', 'messages'])
        self.assertEquals(messages['status'], config.SUCCESS)
        self.assertEquals(messages['messages'], {'member2': [hello_message]})

        # Now we clear the messages
        resp = traverse('@@babblechat/clear_messages')('member2')
        resp = json.loads(resp)
        self.assertEquals(resp['status'], config.SUCCESS)

        messages = utils.get_last_conversation(portal, 'member2')
        self.assertEquals(messages, {'status': config.SUCCESS, 'messages':{}})

        resp = json.loads(traverse('@@babblechat/get_uncleared_messages')())
        self.assertEquals(resp['status'], config.SUCCESS)
        self.assertEquals(resp['messages'], {})

        resp = traverse('@@babblechat/initialize')()
        resp = json.loads(resp)
        self.assertEquals(resp['status'], config.SUCCESS)

        # Test method's response to wrong authentication
        member = self.mtool.getAuthenticatedMember()
        member.chatpass = 'wrongpass'

        method = traverse('@@babblechat/send_message')
        pars = ['member2', 'message']
        self.assertRaises(BabbleException, method, *pars)

        method = traverse('@@babblechat/clear_messages')
        pars = ['member2']
        self.assertRaises(BabbleException, method, *pars)


    def test_utils(self):
        """ Tests some of the utility methods not being tested elsewhere 
        """
        s = 'someone@emailadress.com'
        self.assertEquals(utils.reverse_escape(utils.escape(s)), s)
        s = '& <>\'"'
        self.assertEquals(utils.reverse_escape(utils.escape(s)), s)

        url = 'http://www.someadress.com/here_is_a_very_long-addres?par=LKhase976asg'
        short_url = utils.trim_url(url, 25)
        assert(short_url[:len(short_url)-3] in url)
        self.assertEquals(short_url, url[:22]+'...')

        urlized = utils.urlize(url)
        test_url = u'<a href="http://www.someadress.com/here_is_a_very_long-addres?par=LKhase976asg">http://www.someadress.com/here_is_a_very_long-addres?par=LKhase976asg</a>'
        self.assertEquals(urlized, test_url)

        urlized  = utils.urlize(url, nofollow=True)
        test_url = u'<a href="http://www.someadress.com/here_is_a_very_long-addres?par=LKhase976asg" rel="nofollow">http://www.someadress.com/here_is_a_very_long-addres?par=LKhase976asg</a>'
        self.assertEquals(urlized, test_url)

        urlized = utils.urlize(url, blank=True)
        test_url = u'<a href="http://www.someadress.com/here_is_a_very_long-addres?par=LKhase976asg" target="_blank">http://www.someadress.com/here_is_a_very_long-addres?par=LKhase976asg</a>'
        self.assertEquals(urlized, test_url)

        urlized  = utils.urlize(url, auto_escape=True)
        test_url = u'&lt;a href=&quot;http://www.someadress.com/here_is_a_very_long-addres?par=LKhase976asg&quot;&gt;http://www.someadress.com/here_is_a_very_long-addres?par=LKhase976asg&lt;/a&gt;'
        self.assertEquals(urlized, test_url)

        urlized = utils.urlize(url, nofollow=True, blank=True)
        test_url = u'<a href="http://www.someadress.com/here_is_a_very_long-addres?par=LKhase976asg" rel="nofollow" target="_blank">http://www.someadress.com/here_is_a_very_long-addres?par=LKhase976asg</a>'
        self.assertEquals(urlized, test_url)
        
        urlized = utils.urlize(url, url_limit=5, nofollow=True, blank=True)
        test_url = u'<a href="http://www.someadress.com/here_is_a_very_long-addres?par=LKhase976asg" rel="nofollow" target="_blank">ht...</a>'
        self.assertEquals(urlized, test_url)


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

