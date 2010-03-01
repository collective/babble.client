import logging
import xmlrpclib
from Products.CMFCore.utils import getToolByName
from babble.client import BabbleException
log = logging.getLogger('babble.client/utils.py')

def get_online_contacts(context):
    """ """
    pm = getToolByName(context, 'portal_membership')
    member = pm.getAuthenticatedMember()
    members = pm.listMembers()
    
    if context.portal_javascripts.getDebugMode():
        if member in members:
            members.remove(member)
        return members

    mtool = getToolByName(context, 'portal_chat')
    server = mtool.getConnection()
    try:
        online_contacts = server.getOnlineUsers()
    except xmlrpclib.Fault, e:
        err_msg = e.faultString.strip('\n').split('\n')[-1]
        log.error(\
            'Error from get_online_contacts: server.getOnlineUsers: %s' \
            % err_msg)

        raise BabbleException(err_msg)

    online_members = []
    if member.getId() in online_contacts:
        online_contacts.remove(member.getId())

    for member in members:
        if member.getId() in online_contacts:
            online_members.append(member)
            
    return online_members

