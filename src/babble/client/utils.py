import re
import socket
import urllib
import string
import logging
import simplejson as json
import xmlrpclib
from socket import error as socket_error
from Products.CMFCore.utils import getToolByName

from babble.client import config
from babble.client import iso8601

log = logging.getLogger(__name__)

# Configuration for urlize() function.
LEADING_PUNCTUATION  = ['(', '<', '&lt;']
TRAILING_PUNCTUATION = ['.', ',', ')', '>', '\n', '&gt;']
punctuation_re = re.compile('^(?P<lead>(?:%s)*)(?P<middle>.*?)(?P<trail>(?:%s)*)$' % \
    ('|'.join([re.escape(x) for x in LEADING_PUNCTUATION]),
    '|'.join([re.escape(x) for x in TRAILING_PUNCTUATION])))
simple_email_re = re.compile(r'^\S+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+$')
del x # Temporary variable

def get_string_words(text):
    """ Break up a string into a list of words 
    """
    return re.compile(r'(\s+)').split(text)


def reverse_escape(html):
    """ Returns the given HTML with ampersands, quotes and angle brackets decoded.
    """
    return html.replace(
                '&amp;',  '&').replace(
                '&lt;',   '<').replace(
                '&gt;',   '>').replace(
                '&quot;', '"').replace(
                '&#39;',  "'")

def escape(html):
    """ Returns the given HTML with ampersands, quotes and angle brackets encoded.
    """
    return html.replace(
                '&', '&amp;').replace(
                '<', '&lt;').replace(
                '>', '&gt;').replace(
                '"', '&quot;').replace(
                "'", '&#39;')

def trim_url(url, limit):
    if limit and len(url) > limit:
        return '%s...' % url[:max(0,limit-3)]

    return url


def urlize(text, url_limit=None, nofollow=False, blank=False, auto_escape=False):
    """
    Make HTML <a> tag with the specified URL.

    Works on http://, https://, www. links and links ending in .org, .net or
    .com. 

    Links can have trailing punctuation (periods, commas, close-parens)
    and leading punctuation (opening parens) and it'll still do the right
    thing.

    url_limit:      the length to which URLs must be truncated
    nofolllow:      whether the URLs will get a rel="nofollow" attribute.
    blank:          whether the URLs will get a target="_blank"" attribute.
    auto_escape:    whether URLs will get autoescaped.
    """
    words = get_string_words(text)
    nofollow_attr = nofollow and ' rel="nofollow"' or ''
    blank_attr = blank and ' target="_blank"' or ''
    for i, word in enumerate(words):
        match = None
        if '.' in word or '@' in word or ':' in word:
            match = punctuation_re.match(word)
        if match:
            lead, middle, trail = match.groups()
            url = None
            if middle.startswith('http://') or middle.startswith('https://'):
                url = urllib.quote(middle, safe='/&=:;#?+*')

            elif middle.startswith('www.') or ('@' not in middle and \
                    middle and middle[0] in string.ascii_letters + string.digits and \
                    (middle.endswith('.org') or middle.endswith('.net') or middle.endswith('.com'))):
                url = urllib.quote('http://%s' % middle, safe='/&=:;#?+*')

            elif '@' in middle and not ':' in middle and simple_email_re.match(middle):
                url = 'mailto:%s' % middle
                nofollow_attr = ''

            # Make link.
            if url:
                trimmed = trim_url(middle, url_limit)
                middle = '<a href="%s"%s%s>%s</a>' % (url, nofollow_attr, blank_attr, trimmed)
                if auto_escape:
                    middle = escape(middle)
                words[i] = '%s%s%s' % (lead, middle, trail)
            else:
                if auto_escape:
                    words[i] = escape(word)

    out = ''.join(words)
    try:
        out = unicode(out, 'utf-8')
    except UnicodeDecodeError:
        log.warn("urlize: Could not make unicode out of 'words'")
    return out


def get_connection(context):
    """ Returns a connection to the chat service """
    mtool = getToolByName(context, 'portal_chat')
    return mtool.getConnection()

getConnection = get_connection # BBB


def get_online_usernames(context):
    server = get_connection(context)
    if server is None:
        return []
    try:
        resp = server.getOnlineUsers()
    except xmlrpclib.Fault, e:
        err_msg = e.faultString.strip('\n').split('\n')[-1]
        log.warning(\
            'Error from get_online_usernames: server.getOnlineUsers: %s' \
            % err_msg)
        return []
    except socket_error, e:
        log.warning(\
            'Socket error from get_online_usernames: ' + \
            'server.getOnlineUsers: %s \nis the chatserver running?' \
            %e)
        return []

    online_users = json.loads(resp)['online_users']
    log.debug('get_online_usernames: %s' % str(online_users))
    return online_users


def get_online_members(context):
    """ """
    pm = getToolByName(context, 'portal_membership')
    member = pm.getAuthenticatedMember()
    
    # # XXX: Nice for debugging but confuses people
    # pj = getToolByName(context, 'portal_javascripts')
    # if pj.getDebugMode():
    #     members = pm.listMembers()
    #     log.debug('members: %s' % str(members))
    #     if member in members:
    #         members.remove(member)
    #     return members

    online_users = get_online_usernames(context)
    if member.getId() in online_users:
        online_users.remove(member.getId())

    online_members = []
    for mid in online_users:
        member = pm.getMemberById(mid)
        if member is None:
            continue
        online_members.append(member)

    return online_members


def get_last_conversation(context, audience, chat_type='chatbox'):
    """ Get all the uncleared messages between current member and their 
        audience.
    """
    pm = getToolByName(context, 'portal_membership')
    if pm.isAnonymousUser():
        return config.AUTH_FAIL_RESPONSE
        
    server = get_connection(context)
    if server is None:
        return config.SERVER_ERROR 

    member = pm.getAuthenticatedMember()
    username = member.getId()
    if hasattr(member, 'chatpass'):
        password = getattr(member, 'chatpass') 
    else:
        log.warn("get_last_conversation: %s does not have property 'chatpass'. "
                  "This usually happens when you have deleted and recreated a "
                  "user in Plone, while the Babble ChatService user remains. "
                  "Delete the ChatService user as well and retry. \n"
                  "You can ignore this message during creating of a new Plone site." % username)
        return config.SERVER_ERROR_RESPONSE

    if chat_type == 'chatroom':
        partner = None
        chatrooms = [audience]
    else:
        partner = audience
        chatrooms = []
    try:
        # self, username, password, partner, chatrooms, clear
        return json.loads(server.getUnclearedMessages(
                                username, 
                                password, 
                                partner, 
                                chatrooms,
                                None,
                                False, ))
    except xmlrpclib.Fault, e:
        err_msg = e.faultString.strip('\n').split('\n')[-1]
        log.warn('Error from babble.server: getUnclearedMessages: %s' % err_msg)
        return config.SERVER_ERROR_RESPONSE
        
    except socket.error, e:
        # Catch timeouts so that we can notify the caller
        log.warn(\
            'Socket error from get_last_conversation: ' + \
            'server.getUnclearedMessages: %s \nIs the chatserver running?' %e)
        return config.TIMEOUT_RESPONSE


def get_chat_rooms(context):
    """ """
    mtool = getToolByName(context, 'portal_membership')
    member = mtool.getAuthenticatedMember()
    catalog = getToolByName(context, 'portal_catalog')
    return catalog(
                portal_type='babble.client.chatroom',
                participants=member.getId())
    	

def get_html_formatted_messages(username, messages):
    """ """
    lines = [] 
    for m in messages:
        date = iso8601.parse_date(m[2]).strftime('%Y-%m-%d %H:%M')
        if m[0] != username:
            line = \
                '<div class="chat-message">' + \
                    '<span class="chat-message-them">'+date+' '+m[3]+':&nbsp;&nbsp;</span>' + \
                    '<span class="chat-message-content">'+m[1]+'</span>' + \
                '</div>'
        else:
            line = \
                '<div class="chat-message">' + \
                    '<span class="chat-message-me">'+date+' me:&nbsp;&nbsp;</span>' + \
                    '<span class="chat-message-content">'+m[1]+'</span>' + \
                '</div>'
        lines.append(line)
    return ''.join(lines)


def get_participants(chatroom):
    """ Return the ids of all members who have local roles on the chatroom and
        all members who globally have the manager role.
    """
    plone_utils = getToolByName(chatroom, 'plone_utils')
    roles = plone_utils.getInheritedLocalRoles(chatroom)
    participants = [r[0] for r in roles]
    participants += [r[0] for r in chatroom.get_local_roles()]

    # Replace groups with their members
    portal_groups = getToolByName(chatroom, 'portal_groups')
    for group in portal_groups.getGroupIds():
        if group in participants:
            participants.remove(group)
            participants += portal_groups.getGroupMembers(group)
    return participants

