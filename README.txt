Introduction
============

Babble: Instant Messaging for Plone
-----------------------------------

Babble is an instant messaging service for Plone. 
It consists of babble.client as the Plone front-end client and 
`babble.server <http://plone.org/products/babble.server>`_, 
a Zope2 messaging service, as the backend chat service.

The client consists of an *Online contacts* portlet with which you can initiate 
new chats. Chat sessions occur in modal dialog chatboxes and make use of 
JQuery Ajax polling to provide seamless, real-time messaging.
During inactive periods, the polling interval gradually becomes longer until it
reaches a specific (configurable) maximum polling interval.

Communication between the client and server is achieved with JSON packets 
sent via XML-RPC. 


Features:
---------

- Remembers open chat windows on page reload
- Chat windows can be minimized
- New messages automatically opens chat window
- An 'online users' portlet provides a list of currently online users
- Configurable polling intervals
- Clickable URLs recieved via chat messages
- Requests to the messaging service are password authenticated
- Can be `integrated <http://plone.org/products/actionbar.babble>`_ with the 
  ActionBar of `actionbar.panel <http://plone.org/products/actionbar.panel/>`_
- Can run on a different server than the messaging service


Compatibility:
--------------

Tested to work with Plone 3.3.5 and Plone 4


Documentation:
--------------

Full documentation for the **Babble** project can be found at
http://opkode.net/babbledocs/index.html


TODO:
-----

- Currently Javascript tests can't run anymore because of DTML,
  therefore, consider replacing dtml with collective.xrtresource.
- Add broadcasting (send to all) functionality
- Add tests for URL detection in messages


