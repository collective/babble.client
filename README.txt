Introduction
============

Babble: Instant Messaging for Plone
-----------------------------------

babble.client is an instant messaging client for Plone. It uses babble.server
as its messaging service.

The client makes extensive use of JQuery and Ajax techniques.

Currently, communication with the messaging service is being done via polling.
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

Configuration:
--------------

babble.client needs a running zope instance with a configured babble.server
messaging service.

The client is configured via the portal_chat tool in the ZMI:
- The 'Chat Service URL' field must point to the babble.server messaging service.
- The maximum and minimum polling intervals can also be set in this tool. The
default values are recommended though.


Contact:
--------

Is there vital information lacking in this readme?

Please contact me with questions or suggestions:
brand <at> syslab <dot> com


TODO:
=====

- consider replacing dtml with collective.xrtresource
- consider adding the ability to block certain users.
- consider the ability to set your own status


