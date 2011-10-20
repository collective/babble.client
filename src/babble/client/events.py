from zope.interface import implements
from zope.component.interfaces import ObjectEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent

class ILocalRolesModifiedEvent(IObjectModifiedEvent):
    """The local roles on an event have been modified via the @@sharing page
    """

class LocalRolesModifiedEvent(ObjectEvent):
    """ """
    implements(ILocalRolesModifiedEvent)
