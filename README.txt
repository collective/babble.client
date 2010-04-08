Introduction
============

Babble: Instant Messaging for Plone
-----------------------------------

Babble is an instant messaging service for Plone. 
It consists of babble.client for the Plone front-end and babble.server, 
a Zope2 messaging service, for the backend.

The client consists of an *Online contacts* portlet and modal chatboxes 
that make extensive use of JQuery and Ajax techniques.

Communication between the client and server is done by polling via XML-RPC and JSON.

Server-push options such as Comet, could be considered in the future, but
there is no implementation for this at the moment.


Features:
---------

- Remembers open chat windows on page reload
- Chat windows can be minimized
- New messages automatically opens chat window
- An 'online users' portlet provides a list of currently online users
- Configurable polling intervals
- Requests to the messaging service must be password authenticated
- Can run on a different server than the messaging service
- Well tested. 


Compatibility:
--------------

Confirmed to work with Plone 3.3 and Plone 4


Configuration:
--------------

babble.client needs a running zope instance with a configured babble.server
messaging service. (see the babble.server README)

The client is configured via the portal_chat tool in the ZMI:
- The fields must indicate the babble.server service's particulars.
- The maximum and minimum polling intervals can also be set in this tool. The
default values are recommended though.


How do I start using it?
------------------------

Make sure that babble.client is installed via Plone's control panel, or the
portal_quickinstaller tool in the ZMI (Zope management interface).

In Plone, go to the portlets manage page. In the dropdown of addable portlets,
there should now be a new types of portlet, *Online contacts*.

Add this portlet. If you have more than one person currently using the site,
you should see them appear in this portlet.

Note: When you are running your portal_javascripts registry is in debug mode (or
when you are running './bin/instance fg' in Plone4), then the *Online contacts* 
portlet will show *all* the registered users, and not just the online ones, to make
debugging easier.

Simply click on the user in the portlet, and a chatbox will appear in the
bottom right of the page.

Now start babbling!


actionbar.panel integration:
----------------------------

You can use the chat service with a floating toolbar at the bottom (as
was popularised with Facebook). 

There exists an add-on for actionbar.panel, that provides this functionality.

Simply install actionbar.babble (which will pull in actionbar.panel), to
receive a bottom bar on which the chat windows will dock.


A word of advice:
-----------------

When, working locally or on production, I would recommend 
runnning the messaging service (babble.server) in a
standalone Zope instance or in a separate Zeo client.

Whenever I ran it in the same single non-zeo instance as the client, 
I would have problems with the browser not responding after I 
restart the instance.


Contact:
--------

Is there information lacking in this readme?
Contact me with questions or suggestions:
- brand@syslab.com


TODO:
-----

- Currently Javascripts can't run anymore because of DTML,
  therefore, consider replacing dtml with collective.xrtresource.


