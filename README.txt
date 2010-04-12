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

NOTE: It's recommended that you run the babble.server messaging service in a separate
server or Zeo Client. Running the client and server in the same instance
sometimes causes the browser (and probably Zope/ZPublisher) to become
unresponsive.

IMPORTANT: The babble.server 'Chat Service' object *must* be created in the Zope
root of a Zope instance, not in any Plone root. 

The client is configured via the portal_chat tool in the ZMI:

    - Service name: This is the name of babble.server's 'Chat Service' object that you
      created in the Zope root of the Zope instance you will be using as your
      message server.

    - Host: This is the hostname of the server running the 'Chat Service'. 

    - Port: This is the port number of the server running the 'Chat Service'.

    - Username: This is the username of the Zope user that you used to
      create the 'Chat Service'.

    - Password: This is the password of the Zope user that you used to
      create the 'Chat Service'.


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


Troubleshooting:
----------------

1). *I get a 'connection error' message inside the chat window*

 The 'connection error' message happens whenever the chat client
 (babble.client) cannot communicate with the chat server (babble.server).
 
 This is usually because the chat server is not running (i.e when you
 restart the zope server).
 
 Check that the chat server is running and that your settings in the
 portal_chat tool are correct.

2). *Plone freezes or locks up completely and I have to restart the instance
before this goes away*

 This happens when there is only one Zope instance that has both the
 chat client and the chat server running in it.
 
 The chat client 'polls' the chat server to find new messages. If the
 server stops responding because it is overwhelmed or because it is
 restarted, then the browser hangs forever as it waits for a response, 
 even after Zope was restarted.
 
 The best solution is to run the chat server in a separate dedicated Zeo 
 instance not being used for anything else. 
 
 Make sure to change the port in the portal_chat tool to point to this
 Zeo instance.
 
 A second thing you can do, is to increase the minimum poll time in
 the portal_chat tool, for example from 3000 ms to 6000 ms or more.
 
 This will of course mean that messages can take longer to appear for the
 conversation partners.


Contact:
--------

Is there information lacking in this readme?
Contact me with questions or suggestions:
- brand@syslab.com


TODO:
-----

- Currently Javascript tests can't run anymore because of DTML,
  therefore, consider replacing dtml with collective.xrtresource.


