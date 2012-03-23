Introduction
============

Babble: Instant Messaging for Plone
-----------------------------------

Babble is an instant messaging service for Plone. 
It consists of babble.client as the Plone front-end client and 
`babble.server <http://plone.org/products/babble.server>`_, 
a Zope2-based messaging service, as the backend chat service.

Communication between the client and server is achieved with JSON packets 
sent via XML-RPC. 

The client consists of an *Online contacts* portlet with which you can initiate 
new chats. 

Instead of using the provided portlet, you can also consider using Babble together with
`actionbar.babble <http://plone.org/products/actionbar.babble>`_ .

Chat sessions occur in modal dialog chatboxes and make use of 
JQuery Ajax polling to provide seamless, real-time messaging.

During inactive periods, the polling interval gradually becomes longer until it
reaches a specific (configurable) maximum polling interval.

Please note: even thought the polling values are configurable, it's not advised
to make the minimum polling interval less than 5000 milliseconds.

Features:
---------

- Two-way user communication or chat-rooms for multi-user communication.
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


New feature, Chat Rooms:
-------------------------

A Chat Room can be created just like any other item in Plone, by clicking on the
"Add new" link on the edit bar.

On the Chat Room’s add page, you are asked to provide a Title and an optional
description.

Any person who has permission to view the chat room, will be able to send and
receive instant messages to and from the chat room. This however only applies
to logged in users. 

If an anonymous user has the necessary permissions to view
a chat room, he or she will be able to see the history of the conversation,
but not send or receive messages.

A "Chat Rooms" portlet is available to show the user which chat rooms are
currently available and to open and participate in them.

Note: Chatting in a chat room happens the same was as the two-way chatboxes. The view
of the chat room object only serves as a static record of the conversation.

Compatibility:
--------------

Tested to work with Plone 4


Dependencies:
-------------

Requires babble.server 1.0b5 or higher!


Documentation:
--------------

Full documentation for the **Babble** project can be found at
http://babblechat.org

