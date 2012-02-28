import logging
from zope.component import adapts
from zope.component import queryMultiAdapter

from Products.GenericSetup.interfaces import IBody
from Products.GenericSetup.interfaces import ISetupEnviron
from Products.GenericSetup.utils import PropertyManagerHelpers
from Products.GenericSetup.utils import XMLAdapterBase

from babble.client.interfaces import IBabbleChatTool

log = logging.getLogger(__name__)

_FILENAME = 'babblechat_tool.xml'

class BabbleChatXMLAdapter(XMLAdapterBase, PropertyManagerHelpers):
    """XML im- and exporter for babblechat_tool.
    """
    adapts(IBabbleChatTool, ISetupEnviron)
    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        self.context.host = str(node.getAttribute('host'))
        self.context.port = str(node.getAttribute('port'))
        self.context.service_name = str(node.getAttribute('service_name'))
        self.context.use_local_service = bool(node.getAttribute('use_local_service'))
        self.context.username = str(node.getAttribute('username'))
        self.context.password = str(node.getAttribute('password'))
        self.context.poll_max = str(node.getAttribute('poll_max'))
        self.context.poll_min = str(node.getAttribute('poll_min'))
        log.info('portal_chat properties imported.')


def importBabbleChat(context):
    """Import portal_chat settings from an XML file.
    """
    site = context.getSite()
    body = context.readDataFile(_FILENAME)
    if body is None:
        log.debug('Nothing to import.')
        return

    tool = site.portal_chat
    importer = queryMultiAdapter((tool, context), IBody)
    if importer is None:
        log.warning('Import adapter missing.')
        return

    importer.body = body
