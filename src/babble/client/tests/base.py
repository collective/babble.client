from zope import component

from Products.Five import zcml
from Products.Five import fiveconfigure

from plone import browserlayer

from Products.Archetypes.Schema.factory import instanceSchemaFactory
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase import layer 

from babble.client.interfaces import IBabbleClientLayer

SiteLayer = layer.PloneSite

class BabbleClientLayer(SiteLayer):

    @classmethod
    def setUp(cls):
        """ Set up the additional products required for the 
            DubletteFinder.
        """
        PRODUCTS = [
                'babble.server',
                'babble.client',
                ]
        ptc.setupPloneSite(products=PRODUCTS)

        fiveconfigure.debug_mode = True
        import babble.server
        zcml.load_config('configure.zcml', babble.server)
        import babble.client
        zcml.load_config('configure.zcml', babble.client)
        fiveconfigure.debug_mode = False
        
        browserlayer.utils.register_layer(IBabbleClientLayer, name='babble.client')

        component.provideAdapter(instanceSchemaFactory)
        SiteLayer.setUp()
    

class TestCase(ptc.PloneTestCase):
    """Base class used for test cases
    """
    layer = BabbleClientLayer


