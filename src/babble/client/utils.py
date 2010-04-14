import logging
from socket import error as socket_error
import xmlrpclib
import simplejson as json
from Products.CMFCore.utils import getToolByName
log = logging.getLogger('babble.client/utils.py')

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
    
    if context.portal_javascripts.getDebugMode():
        if member in members:
            members.remove(member)
        return members

    online_users = get_online_usernames(context)
    online_members = []
    if member.getId() in online_users:
        online_users.remove(member.getId())

    for member in members:
        if member.getId() in online_users:
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

