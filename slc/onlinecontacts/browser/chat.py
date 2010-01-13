import logging
import simplejson as json
from Products.CMFCore.utils import getToolByName

log = logging.getLogger('slc.onlinecontacts/browser/chat.py')

class Chat:

    def _authenticated_member(self):
        """ """
        pm = getToolByName(self, 'portal_membership')
        return pm.getAuthenticatedMember()

    def send_chat(self, to, message):
        """ Send a chat message """
        log.info('Chat message %s sent to %s' % (message, to))

    def poll(self):
        """ Polling to retrieve online users and chat messages """
        log.info('poll called')
        return json.dumps({'items': []})

    def start_session(self):
        """ Polling to retrieve online users and chat messages """
        log.info('start_session called')
        member = self._authenticated_member()
        return json.dumps({'username': member.id, 'items': []})
