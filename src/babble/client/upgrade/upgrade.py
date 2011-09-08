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

