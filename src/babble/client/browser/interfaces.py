from zope.interface import Interface

class IChat(Interface):

    def initialize(self, username=None):
        """ Check if the user is registered, and register if not
        """

    def get_uncleared_messages(self, audience='*', mark_cleared=False):
        """ Retrieve the uncleared messages from the chat server 
        """

    def poll(self, username):
        """ Poll the chat server to retrieve new online users and chat
            messages
        """

    def send_message(self, to, message, chat_type='chatbox'):
        """ Send a chat message 
        """

    def clear_messages(self, audience):
        """ Mark the messages in a chat contact's messagebox as cleared.
            This means that they won't be loaded and displayed again next time
            that chat box is opened.
        """


class IChatBox(Interface):
    """ """

    def reverse_escape(self, html):
        """ """

    def render_chat_box(self, box_id, user, contact):
        """ """

