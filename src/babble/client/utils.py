import re
import urllib
import string
import logging
import simplejson as json
import xmlrpclib
from socket import error as socket_error
from Products.CMFCore.utils import getToolByName

log = logging.getLogger('babble.client/utils.py')

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
    """ Returns the given HTML with ampersands, quotes and angle brackets encoded.
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
    Adapted from a similar method in Django

    Works on http://, https://, www. links and links ending in .org, .net or
    .com. Links can have trailing punctuation (periods, commas, close-parens)
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
        log.error("urllize: Could not make unicode out of 'words'")
    return out


def getConnection(context):
    """ Returns a connection to the chat service """
    mtool = getToolByName(context, 'portal_chat')
    return mtool.getConnection()


def get_online_usernames(context):
    server = getConnection(context)
    try:
        resp = server.getOnlineUsers()
    except xmlrpclib.Fault, e:
        err_msg = e.faultString.strip('\n').split('\n')[-1]
        log.error(\
            'Error from get_online_contacts: server.getOnlineUsers: %s' \
            % err_msg)
        return []
    except socket_error, e:
        log.error(\
            'Socket error from get_online_contacts:' + \
            'server.getOnlineUsers: %s \nis the chatserver running?' \
            %e)
        return []

    resp = json.loads(resp)
    return resp['online_users']


def get_online_members(context):
    """ """
    pm = getToolByName(context, 'portal_membership')
    member = pm.getAuthenticatedMember()
    members = pm.listMembers()
    
    # XXX: Nice for debugging but confuses people
    #
    # pj = getToolByName(context, 'portal_javascripts')
    # if pj.getDebugMode():
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


def get_last_conversation(context, contact):
    """ Get all the uncleared messages between current member and contact
    """
    pm = getToolByName(context, 'portal_membership')
    if pm.isAnonymousUser():
        return {}

    server = getConnection(context)
    member = pm.getAuthenticatedMember()
    username = member.getId()
    if hasattr(member, 'chatpass'):
        password = getattr(member, 'chatpass') 
    else:
        log.error("get_last_conversation: %s does not have prop 'chatpass'"
                                                                    % username)
        return {}

    try:
        #pars: username, sender, read, clear
        resp = server.getUnclearedMessages(
                            username, password, contact, True, False)

    except xmlrpclib.Fault, e:
        err_msg = e.faultString.strip('\n').split('\n')[-1]
        log.error('Error from chat.service: clearMessages: %s' % err_msg)
        return {}
    
    resp = json.loads(resp)
    return resp['messages']

    	
