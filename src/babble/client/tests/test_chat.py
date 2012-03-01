# coding: UTF-8
import datetime
import re
import simplejson as json
from pytz import utc
from zope.interface import alsoProvides
from OFS.Folder import Folder
from babble.client import utils
from babble.client.interfaces import IBabbleClientLayer
from babble.client.tests.base import TestCase
from babble.server import config 

# Regex to test for ISO8601, i.e: '2011-09-30T15:49:35.417693+00:00'
RE = re.compile(r'^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}\.\d{6}[+-]\d{2}:\d{2}$')

class TestChat(TestCase):
    """ Tests the babble/client/browser/chat.py module
    """

    def _test_online_users(self, username1, username2):
        """ Tests the confirm_as_online, get_online_usernames and 
            get_online_members methods
        """
        portal = self.portal

        # First clear the UAD
        server = utils.getConnection(self.portal)
        server._v_user_access_dict = {}
    
        online_users = utils.get_online_usernames(portal)
        self.assertEquals(online_users, [])

        online_members = utils.get_online_members(portal)
        self.assertEquals(online_members, [])

        self.logout()
        resp = json.loads(server.confirmAsOnline(None))
        self.assertEquals(resp['status'], config.ERROR)

        self.login(name=username1)

        server = utils.getConnection(self.portal)
        resp = json.loads(server.confirmAsOnline(username1))
        self.assertEquals(resp['status'], config.SUCCESS)

        online_users = utils.get_online_usernames(portal)
        self.assertEquals(online_users, [username1])

        # get_online_members ignores the currently logged in user.
        # So, if username1 is currently logged in and also online (according to
        # get_online_users), get_online_members will still return an empty
        # list.
        online_members = utils.get_online_members(portal)
        self.assertEquals(online_members, [])

        self.logout()

        self.login(name=username2)

        server = utils.getConnection(self.portal)
        resp = json.loads(server.confirmAsOnline(username2))
        self.assertEquals(resp['status'], config.SUCCESS)

        online_users = utils.get_online_usernames(portal)
        online_users.sort()
        self.assertEquals(online_users, [username1, username2])

        # Again, the logged in username2 is ignored
        member1 = self.mtool.getMemberById(username1)
        online_members = utils.get_online_members(portal)
        self.assertEquals(online_members, [member1])
        self.logout()

        # Now the logged in username1 is ignored
        self.login(name=username1)
        member2 = self.mtool.getMemberById(username2)
        online_members = utils.get_online_members(portal)
        self.assertEquals(online_members, [member2])

    def _test_messaging(self, username1, username2):
        """ Base class, to allow different usernames (email vs normal) to be
            used.
        """
        portal = self.portal
        traverse = portal.restrictedTraverse

        # Make sure username1 is registered on the chatserver by calling
        # initialize
        self.login(name=username1)
        resp = traverse('@@babblechat/initialize')()
        resp = json.loads(resp)
        self.assertEquals(resp['status'], config.SUCCESS)
        
        # Test some methods' handling of anon users
        self.logout()
        resp = traverse('@@babblechat/initialize')()
        resp = json.loads(resp)
        self.assertEquals(resp['status'], config.AUTH_FAIL)

        member = self.mtool.getAuthenticatedMember()
        resp = traverse('@@babblechat/poll')(member.getId(), config.NULL_DATE)
        resp = json.loads(resp)
        self.assertEquals(resp['status'], config.AUTH_FAIL)
        resp = traverse('@@babblechat/send_message')(username1, 'message')
        resp = json.loads(resp)
        self.assertEquals(resp['status'], config.AUTH_FAIL)
        resp = traverse('@@babblechat/clear_messages')(username1, 'chatbox', datetime.datetime.now(utc).isoformat())
        resp = json.loads(resp)
        self.assertEquals(resp['status'], config.AUTH_FAIL)

        messages = utils.get_last_conversation(portal, username1)
        self.assertEquals(messages['status'], config.AUTH_FAIL)

        # Test methods' response to a user ('portal_owner') who wasn't
        # initialized
        self.logout()
        self.loginAsPortalOwner()

        member = self.mtool.getAuthenticatedMember()
        resp = traverse('@@babblechat/poll')(member.getId(), config.NULL_DATE)
        resp = json.loads(resp)
        self.assertEquals(resp['status'], config.AUTH_FAIL)

        resp = traverse('@@babblechat/send_message')(username1, 'message')
        resp = json.loads(resp)
        self.assertEquals(resp['status'], config.AUTH_FAIL)

        method = traverse('@@babblechat/clear_messages')
        pars = [username1, 'chatbox', datetime.datetime.now(utc)]
        self.assertRaises(AttributeError, method, *pars)

        messages = utils.get_last_conversation(portal, username1)
        self.assertEquals(messages['status'], config.ERROR)
        
        # Make sure username2 is registered on the chatserver by calling
        # initialize
        self.login(name=username2)
        resp = traverse('@@babblechat/initialize')()
        resp = json.loads(resp)
        self.assertEquals(resp['status'], config.SUCCESS)

        # Send a message from username2 to username1 and note the time so that we
        # can test for it later on
        timeminutes = datetime.datetime.now(utc).strftime("%H:%M")
        resp = traverse('@@babblechat/send_message')(username1, 'hello')
        resp = json.loads(resp)
        self.assertEquals(resp['status'], config.SUCCESS)
        self.assertEqual(bool(RE.search(resp['last_msg_date'])), True)
        message_timestamp = resp['last_msg_date']

        # Poll for username1 and see if we got our message
        self.login(name=username1)
        resp = traverse('@@babblechat/poll')(username1, config.NULL_DATE)
        resp = json.loads(resp)
        self.assertEquals(resp['status'], config.SUCCESS)
        self.assertEquals(resp['last_msg_date'], message_timestamp)
        # Check that a message was received from username2
        self.assertEquals(resp['messages'].keys(), [username2])
        # Check the message format
        hello_message = [username2, 'hello', 'dummydate']
        member2 = self.mtool.getMemberById(username2)
        # {
        #     'chatroom_messages': {},
        #     'last_msg_date': '2011-11-19T12:43:34.922511+00:00',
        #     'messages': {
        #             'member2': [['member2', 'hello', '2011-11-19T12:43:34.922511+00:00', 'Member2']]
        #             },
        #     'status': 0
        # }
        self.assertEquals(resp['messages'][username2][0][-1], member2.getProperty('fullname', username2).decode('utf-8'))
        self.assertEquals(resp['messages'][username2][0][0], hello_message[0])
        self.assertEquals(resp['messages'][username2][0][1], hello_message[1])
        # Check that the last item in the message tuple is an iso8601 timestamp
        self.assertEqual(bool(RE.search(resp['messages'][username2][0][2])), True)
        self.assertEqual(resp['messages'][username2][0][2], message_timestamp)

        # Check that the next poll (with new timestamp) returns no new messages
        resp = traverse('@@babblechat/poll')(username1, message_timestamp)
        resp = json.loads(resp)
        self.assertEquals(resp['status'], config.SUCCESS)
        self.assertEquals(resp['messages'], {})

        # Check that calling get_uncleared_messages will return the original message,
        # since it has not been cleared
        resp = traverse('@@babblechat/get_uncleared_messages')()
        resp = json.loads(resp)
        messages = resp['messages']
        self.assertEquals(resp['status'], config.SUCCESS)
        self.assertEquals(resp['messages'][username2][0][-1], member2.getProperty('fullname', username2).decode('utf-8'))
        self.assertEquals(resp['messages'][username2][0][0], hello_message[0])
        self.assertEquals(resp['messages'][username2][0][1], hello_message[1])
        # Check that the last item in the message tuple is an iso8601 timestamp
        self.assertEqual(bool(RE.search(resp['messages'][username2][0][2])), True)
        self.assertEqual(resp['messages'][username2][0][2], message_timestamp)

        # Also test that utils' get_last_conversation returns this message
        messages = utils.get_last_conversation(portal, username2)
        self.assertEquals(messages.keys(), ['status', 'messages', 'last_msg_date', 'chatroom_messages'])
        self.assertEquals(messages['status'], config.SUCCESS)
        self.assertEquals(resp['messages'][username2][0][0], hello_message[0])
        self.assertEquals(resp['messages'][username2][0][1], hello_message[1])
        self.assertEqual(bool(RE.search(resp['messages'][username2][0][2])), True)
        self.assertEqual(resp['messages'][username2][0][2], message_timestamp)

        # Now we clear the messages
        resp = traverse('@@babblechat/clear_messages')(username2, 'chatbox', datetime.datetime.now(utc).isoformat())
        resp = json.loads(resp)
        self.assertEquals(resp['status'], config.SUCCESS)

        messages = utils.get_last_conversation(portal, username2)

        check = {'status': config.SUCCESS, 'last_msg_date': message_timestamp, 'messages':{}, 'chatroom_messages': {}}
        self.assertEquals(messages, check)

        resp = json.loads(traverse('@@babblechat/get_uncleared_messages')())
        self.assertEquals(resp['status'], config.SUCCESS)
        self.assertEquals(resp['messages'], {})

        resp = traverse('@@babblechat/initialize')()
        resp = json.loads(resp)
        self.assertEquals(resp['status'], config.SUCCESS)

        # Test method's response to wrong authentication
        member = self.mtool.getAuthenticatedMember()
        member.chatpass = 'wrongpass'

        resp = traverse('@@babblechat/send_message')(username2, 'message')
        resp = json.loads(resp)
        self.assertEquals(resp['status'], config.AUTH_FAIL)

        resp = traverse('@@babblechat/clear_messages')(username2, 'chatbox', datetime.datetime.now(utc).isoformat())
        resp = json.loads(resp)
        self.assertEquals(resp['status'], config.AUTH_FAIL)

        resp = json.loads(traverse('@@babblechat/get_uncleared_messages')(username2))
        self.assertEquals(resp['status'], config.AUTH_FAIL)


    def test_online_users(self):
        """ Tests the confirm_as_online, get_online_usernames and 
            get_online_members methods
        """
        self._test_online_users('member1', 'member2')


    def test_messaging(self):
        """ Test message sending
        """
        self._test_messaging('member1', 'member2')


    def test_utils(self):
        """ Tests some of the utility methods not being tested elsewhere 
        """
        s = '& <>\'"'
        self.assertEquals(utils.escape(s), '&amp; &lt;&gt;&#39;&quot;')
        self.assertEquals(utils.reverse_escape(utils.escape(s)), s)

        s = "Here is a list of words"
        l = ["Here", " ", "is", " ", "a", " ", "list", " ", "of", " ", "words"]
        self.assertEquals(utils.get_string_words(s), l) 

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



class TestEmailLoginChat(TestChat):
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
        self.site_props = self.portal.portal_properties.site_properties
        self.site_props._updateProperty('use_email_as_login', True)
        self.create_user('member1', 'secret')
        self.create_user('member2', 'secret')
        self.create_user('member3@example.com', 'secret')
        self.create_user('member4@example.com', 'secret')
        self.create_user(u'roché', 'secret')
        self.create_user(u'störtebeker', 'secret')
        # Merely registering babble.client's browserlayer doesn't set it on the
        # request. This happens during IBeforeTraverseEvent, so we have to do 
        # it here manually
        alsoProvides(self.portal.REQUEST, IBabbleClientLayer)

    def test_online_users_with_email_usernames(self):
        """ Same as test_messaging but with email usernames 
        """
        self._test_online_users('member3@example.com', 'member4@example.com')

    def test_messaging_with_email_usernames(self):
        """ Same as test_messaging but with email usernames 
        """
        self._test_messaging('member3@example.com', 'member4@example.com')

    def test_online_users_with_non_ascii_usernames(self):
        """ Same as test_messaging but with email usernames 
        """
        self._test_messaging(u'roché', u'störtebeker')

    def test_messaging_with_non_ascii_usernames(self):
        """ Same as test_messaging but with email usernames 
        """
        self._test_messaging(u'roché', u'störtebeker')


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestChat))
    suite.addTest(makeSuite(TestEmailLoginChat))
    return suite

