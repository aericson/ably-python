from __future__ import absolute_import

import base64
import hashlib
import hmac
import json
import logging
import random
import time

import six

from ably.types.capability import Capability
from ably.types.tokendetails import TokenDetails
from ably.types.tokenrequest import TokenRequest

# initialise and seed our own instance of random
rnd = random.Random()
rnd.seed()

from ably.util.exceptions import AblyException

__all__ = ["Auth"]

log = logging.getLogger(__name__)


class Auth(object):

    class Method:
        BASIC = "BASIC"
        TOKEN = "TOKEN"

    def __init__(self, ably, options):
        self.__ably = ably
        self.__auth_options = options

        self.__basic_credentials = None
        self.__auth_params = None
        self.__token_details = None

        must_use_token_auth = options.use_token_auth is True
        must_not_use_token_auth = options.use_token_auth is False
        can_use_basic_auth = options.key_secret is not None and options.client_id is None
        if not must_use_token_auth and can_use_basic_auth:
            # We have the key, no need to authenticate the client
            # default to using basic auth
            log.debug("anonymous, using basic auth")
            self.__auth_method = Auth.Method.BASIC
            basic_key = "%s:%s" % (options.key_name, options.key_secret)
            basic_key = base64.b64encode(basic_key.encode('utf-8'))
            self.__basic_credentials = basic_key.decode('ascii')
            return
        elif must_not_use_token_auth and not can_use_basic_auth:
            raise ValueError('If use_token_auth is False you must provide a key')

        # Using token auth
        self.__auth_method = Auth.Method.TOKEN

        if options.token_details:
            self.__token_details = options.token_details
        elif options.auth_token:
            self.__token_details = TokenDetails(token=options.auth_token)
        else:
            self.__token_details = None

        if options.auth_callback:
            log.debug("using token auth with auth_callback")
        elif options.auth_url:
            log.debug("using token auth with auth_url")
        elif options.key_secret:
            log.debug("using token auth with client-side signing")
        elif options.auth_token:
            log.debug("using token auth with supplied token only")
        elif options.token_details:
            log.debug("using token auth with supplied token_details")
        else:
            raise ValueError("Can't authenticate via token, must provide "
                             "auth_callback, auth_url, key, token or a TokenDetail")

    def authorise(self, token_params=None, auth_options=None):
        if token_params is None:
            token_params = {}
        if auth_options is None:
            auth_options = {}
        self.__auth_method = Auth.Method.TOKEN

        force = auth_options.pop('force', False)

        if self.__token_details:
            if (self.__token_details.expires is None or
                    self.__token_details.expires > self._timestamp()):
                if not force:
                    if self.__token_details.expires is not None:
                        log.debug(
                            "using cached token; expires = %d",
                            self.__token_details.expires
                        )
                    return self.__token_details
            else:
                # token has expired
                self.__token_details = None

        self.__token_details = self.request_token(token_params, auth_options)
        return self.__token_details

    def request_token(self, token_params=None, auth_options=None):
        if token_params is None:
            token_params = {}
        if auth_options is None:
            auth_options = {}

        key_name = auth_options.get('key_name') or self.auth_options.key_name
        key_secret = auth_options.get('key_secret') or self.auth_options.key_secret

        auth_callback = auth_options.get('auth_callback') or self.auth_options.auth_callback
        log.debug("Auth callback: %s" % auth_callback)
        log.debug("Auth options: %s" % six.text_type(self.auth_options))
        query_time = auth_options.get('query_time') or self.auth_options.query_time
        query_time = bool(query_time)
        auth_url = auth_options.get('auth_url') or self.auth_options.auth_url
        auth_headers = auth_options.get('auth_headers')

        token_params = token_params or {}

        token_params.setdefault("client_id", self.ably.client_id)

        signed_token_request = ""

        log.debug("Token Params: %s" % token_params)
        if auth_callback:
            log.debug("using token auth with authCallback")
            signed_token_request = auth_callback(**token_params)
        elif auth_url:
            log.debug("using token auth with authUrl")
            response = self.ably.http.post(
                auth_url,
                headers=auth_headers,
                native_data=token_params,
                skip_auth=True
            )

            AblyException.raise_for_response(response)

            signed_token_request = response.text
        elif key_secret:
            log.debug("using token auth with client-side signing")
            signed_token_request = self.create_token_request(
                auth_options=auth_options,
                token_params=token_params).hash
        else:
            log.debug('No auth_callback, auth_url or key_secret specified')
            raise AblyException(
                "Auth.request_token() must include valid auth parameters",
                400,
                40000)

        token_path = "/keys/%s/requestToken" % key_name

        response = self.ably.http.post(
            token_path,
            headers=auth_headers,
            native_data=signed_token_request,
            skip_auth=True
        )

        AblyException.raise_for_response(response)
        response_dict = response.to_native()
        log.debug("Token: %s" % str(response_dict.get("token")))
        return TokenDetails.from_dict(response_dict)

    def create_token_request(self, token_params=None, auth_options=None):
        if token_params is None:
            token_params = {}
        if auth_options is None:
            auth_options = {}

        key_name = auth_options.get('key_name') or self.auth_options.key_name
        key_secret = auth_options.get('key_secret') or self.auth_options.key_secret

        if token_params.setdefault("id", key_name) != key_name:
            raise AblyException("Incompatible key specified", 401, 40102)

        if not key_name or not key_secret:
            log.debug('key_name or key_secret blank')
            raise AblyException("No key specified", 401, 40101)

        query_time = auth_options.get('query_time') or self.auth_options.query_time

        if not token_params.get("timestamp"):
            if query_time:
                token_params["timestamp"] = self.ably.time()
            else:
                token_params["timestamp"] = self._timestamp()

        token_params["timestamp"] = int(token_params["timestamp"])

        if token_params.get("capability") is None:
            token_params["capability"] = ""
        else:
            token_params['capability'] = six.text_type(
                Capability(token_params["capability"])
            )

        if token_params.get("client_id") is None:
            token_params["client_id"] = ""

        if not token_params.get("nonce"):
            # Note: There is no expectation that the client
            # specifies the nonce; this is done by the library
            # However, this can be overridden by the client
            # simply for testing purposes
            token_params["nonce"] = self._random()

        req = {
            "keyName": key_name,
            "capability": token_params["capability"],
            "client_id": token_params["client_id"],
            "timestamp": token_params["timestamp"],
            "nonce": token_params["nonce"]
        }

        if token_params.get("ttl"):
            req["ttl"] = token_params["ttl"]

        if not token_params.get("mac"):
            # Note: There is no expectation that the client
            # specifies the mac; this is done by the library
            # However, this can be overridden by the client
            # simply for testing purposes.
            sign_text = six.u("\n").join([six.text_type(x) for x in [
                token_params["id"],
                token_params.get("ttl", ""),
                token_params["capability"],
                token_params["client_id"],
                "%d" % token_params["timestamp"],
                token_params.get("nonce", ""),
                "",  # to get the trailing new line
            ]])
            key_secret = key_secret.encode('utf8')
            sign_text = sign_text.encode('utf8')
            log.debug("Key value: %s" % key_secret)
            log.debug("Sign text: %s" % sign_text)

            mac = hmac.new(key_secret, sign_text, hashlib.sha256).digest()
            mac = base64.b64encode(mac).decode('utf8')
            token_params["mac"] = mac

        req["mac"] = token_params.get("mac")

        signed_request = TokenRequest(req)

        return signed_request

    @property
    def ably(self):
        return self.__ably

    @property
    def auth_method(self):
        return self.__auth_method

    @property
    def auth_options(self):
        return self.__auth_options

    @property
    def auth_params(self):
        return self.__auth_params

    @property
    def basic_credentials(self):
        return self.__basic_credentials

    @property
    def token_credentials(self):
        if self.__token_details:
            token = self.__token_details.token
            token_key = base64.b64encode(token.encode('utf-8'))
            return token_key.decode('ascii')

    @property
    def token_details(self):
        return self.__token_details

    def _get_auth_headers(self):
        if self.__auth_method == Auth.Method.BASIC:
            return {
                'Authorization': 'Basic %s' % self.basic_credentials,
            }
        else:
            self.authorise()
            return {
                'Authorization': 'Bearer %s' % self.token_credentials,
            }

    def _timestamp(self):
        """Returns the local time in milliseconds since the unix epoch"""
        return int(time.time() * 1000)

    def _random(self):
        return "%016d" % rnd.randint(0, 9999999999999999)
