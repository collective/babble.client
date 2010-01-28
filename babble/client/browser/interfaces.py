from zope.interface import Interface

class IChat(Interface):

    def _getConnection(self):
        """ Returns a connection to the chat service """

    def _authenticated_member(self):
        """ Returns the currently logged in member object """

    def start_session(self, open_chats):
        """ Initializion by fetching all open chat sessions and their uncleared 
            and unread chat messages
        """

    def poll(self, user):
        """ Poll the chat server to retrieve new online users and chat 
            messages 
        """

    def send_message(self, user, to, message):
        """ Send a chat message """

    def get_last_conversation(self, user, chat_buddy):
        """ Get all the uncleared messages between user and chat_buddy 
        """

    def clear_messages(self, member, chat_buddy):
        """ Mark the messages in a chat contact's messagebox as cleared. 
            This means that they won't be loaded and displayed again next time 
            that chat box is opened.
        """

