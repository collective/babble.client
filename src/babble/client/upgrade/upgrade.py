import logging
from Acquisition import aq_parent
from Products.CMFCore.utils import getToolByName

log = logging.getLogger(__name__)

def updateResourcePaths(context):
    siteroot = aq_parent(context)
    context.runImportStepFromProfile("profile-babble.client:default", "jsregistry", True)
    log.info("Reloaded JS registry.")
    context.runImportStepFromProfile("profile-babble.client:default", "cssregistry", True)
    log.info("Reloaded CSS registry.")

    jstool = getToolByName(context, 'portal_javascripts')
    jstool.unregisterResource('++resource++quicksearch.js')
    jstool.unregisterResource('++resource++jquery.cookie.js')
    jstool.unregisterResource('++resource++jquery.ba-dotimeout.js')
    jstool.unregisterResource('++resource++jquery.ba-dotimeout.min.js')

    csstool = getToolByName(context, 'portal_css')
    csstool.unregisterResource('++resource++chat.css')
    log.info("Removed old js and css resources")

def renameChatTool(context):
    site = aq_parent(context)
    context.runImportStepFromProfile("profile-babble.client:default", "toolset", True)
    log.info("Reloaded toolset.xml")

    if hasattr(site, 'portal_chat'):
        oldtool = site.portal_chat
        newtool = site.portal_babblechat

        newtool.host = oldtool.host
        newtool.port = oldtool.port
        newtool.service_name = oldtool.name
        newtool.username = oldtool.username
        newtool.password = oldtool.password
        newtool.poll_max = oldtool.poll_max
        newtool.poll_min = oldtool.poll_min
        
        site.manage_delObjects(['portal_chat'])
        log.info("Removed old tool portal_chat")

