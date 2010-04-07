from zope.interface import Interface

class IChat(Interface):

    def confirm_as_online(self):
        """ Let the chat server know that the currently authenticated used is
            still online 
        """

    def initialize(self):
        """ Initializion by fetching all open chat sessions and their uncleared
            and unread chat messages
        """

    def poll(self):
        """ Poll the chat server to retrieve new online users and chat
            messages
        """

    def send_message(self, to, message):
        """ Send a chat message """


    def clear_messages(self, contact):
        """ Mark the messages in a chat contact's messagebox as cleared.
            This means that they won't be loaded and displayed again next time
            that chat box is opened.
        """

class IChatBox(Interface):
    """ """

    def render_chat_box(self, box_id, user, contact):
        """ """

