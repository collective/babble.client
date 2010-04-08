from zope import component

from Products.Five import zcml
from Products.Five import fiveconfigure

from Testing import ZopeTestCase as ztc

from plone import browserlayer

from Products.Archetypes.Schema.factory import instanceSchemaFactory
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase import layer 

from babble.client.interfaces import IBabbleClientLayer

import Products.Five
ztc.installProduct('Five')
zcml.load_config('configure.zcml', package=Products.Five)

ztc.installProduct('babble.server')
ztc.installPackage('babble.server')

ztc.installPackage('collective.js.blackbird')
ztc.installPackage('babble.client')

SiteLayer = layer.PloneSite

class BabbleClientLayer(SiteLayer):

    @classmethod
    def setUp(cls):
        """ Set up the additional products required for the 
            DubletteFinder.
        """
        PRODUCTS = [
                'collective.js.blackbird',
                'babble.server',
                'babble.client',
                ]
        ptc.setupPloneSite(products=PRODUCTS)

        fiveconfigure.debug_mode = True
        import collective.js.blackbird
        zcml.load_config('configure.zcml', collective.js.blackbird)
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


