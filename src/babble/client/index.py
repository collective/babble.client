from plone.indexer import indexer
from Products.CMFCore.utils import getToolByName
from babble.client.chatroom import IChatRoom

@indexer(IChatRoom)
def participants(chatroom):
    """ Return all users and groups who have a local role on the chatroom.
    """
    plone_utils = getToolByName(chatroom, 'plone_utils')
    roles = plone_utils.getInheritedLocalRoles(chatroom)
    inherited_roles = [r[0] for r in roles]
    participants = \
        [r[0] for r in chatroom.get_local_roles() if r[0] not in inherited_roles]
    participants += inherited_roles
    return participants
