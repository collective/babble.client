I18N_DOMAIN = 'babble.client'
SUCCESS = 0
AUTH_FAIL = -1
TIMEOUT = 1
SERVER_ERROR = SERVER_FAULT = 2
NOT_FOUND = 3

from datetime import datetime
from pytz import utc
NULL_DATE = datetime.min.replace(tzinfo=utc).isoformat()

AUTH_FAIL_RESPONSE = {
    'status': AUTH_FAIL, 
    'last_msg_date': NULL_DATE, 
    'chatroom_messages': {},
    'messages': {}
    }

SERVER_ERROR_RESPONSE = {
    'status': SERVER_ERROR, 
    'last_msg_date': NULL_DATE, 
    'chatroom_messages': {},
    'messages': {}
    }

TIMEOUT_RESPONSE = {
    'status': TIMEOUT, 
    'last_msg_date': NULL_DATE, 
    'chatroom_messages': {},
    'messages': {}
    }

