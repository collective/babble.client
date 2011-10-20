I18N_DOMAIN = 'babble.client'

SUCCESS = 0
AUTH_FAIL = -1
TIMEOUT = 1
SERVER_FAULT = 2
NOT_FOUND = 3

from datetime import datetime
from pytz import utc
NULL_DATE = datetime.min.replace(tzinfo=utc).isoformat()

