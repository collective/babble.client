from zope.i18nmessageid import MessageFactory
from babble.client.config import I18N_DOMAIN
BabbleMessageFactory = MessageFactory(I18N_DOMAIN)

class BabbleException(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

