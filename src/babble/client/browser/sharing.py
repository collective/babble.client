from zope.event import notify
from plone.app.workflow.browser import sharing
from babble.client.events import LocalRolesModifiedEvent

class SharingView(sharing.SharingView):
    """ """

    def update_role_settings(self, new_settings, reindex=True):
        changed = \
            super(SharingView, self).update_role_settings(new_settings, reindex)

        event = LocalRolesModifiedEvent(self.context)
        notify(event)




