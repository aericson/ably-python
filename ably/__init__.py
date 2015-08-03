import logging

import sys

logger = logging.getLogger(__name__)
if (not sys.argv[0].endswith('nosetests') and
        not (sys.argv[0].endswith('setup.py') and 'test' in sys.argv)):
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.WARNING)

requests_log = logging.getLogger('requests')
requests_log.setLevel(logging.WARNING)

from ably.rest.rest import AblyRest
from ably.rest.auth import Auth
from ably.types.capability import Capability
from ably.types.channeloptions import ChannelOptions
from ably.types.options import Options
from ably.util.crypto import CipherParams
from ably.util.exceptions import AblyException
