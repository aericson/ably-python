from __future__ import absolute_import

import logging
import unittest

from ably import AblyRest
from ably import Auth
from ably import Options

from ably.types.tokendetails import TokenDetails

from test.ably.restsetup import RestSetup

test_vars = RestSetup.get_test_vars()


log = logging.getLogger(__name__)


class TestAuth(unittest.TestCase):

    def test_auth_init_key_only(self):
        ably = AblyRest(key=test_vars["keys"][0]["key_str"])
        self.assertEqual(Auth.Method.BASIC, ably.auth.auth_method,
                         msg="Unexpected Auth method mismatch")

    def test_auth_init_token_only(self):
        ably = AblyRest(token="this_is_not_really_a_token")

        self.assertEqual(Auth.Method.TOKEN, ably.auth.auth_method,
                         msg="Unexpected Auth method mismatch")

    def test_auth_init_with_token_callback(self):
        callback_called = []

        def token_callback(**params):
            callback_called.append(True)
            return "this_is_not_really_a_token_request"

        ably = AblyRest(key_name=test_vars["keys"][0]["key_name"],
                        host=test_vars["host"],
                        port=test_vars["port"],
                        tls_port=test_vars["tls_port"],
                        tls=test_vars["tls"],
                        auth_callback= token_callback)

        try:
            ably.stats(None)
        except:
            pass

        self.assertTrue(callback_called, msg="Token callback not called")
        self.assertEqual(Auth.Method.TOKEN, ably.auth.auth_method,
                msg="Unexpected Auth method mismatch")
        
    def test_auth_init_with_key_and_client_id(self):
        options = Options(key=test_vars["keys"][0]["key_str"])

        ably = AblyRest(key=test_vars["keys"][0]["key_str"], client_id='testClientId')

        self.assertEqual(Auth.Method.TOKEN, ably.auth.auth_method,
                msg="Unexpected Auth method mismatch")

    def test_auth_init_with_token(self):

        ably = AblyRest(token="this_is_not_really_a_token",
                        host=test_vars["host"],
                        port=test_vars["port"],
                        tls_port=test_vars["tls_port"],
                        tls=test_vars["tls"])

        self.assertEqual(Auth.Method.TOKEN, ably.auth.auth_method,
                msg="Unexpected Auth method mismatch")

    def test_use_token_auth_can_be_enabled(self):
        ably = AblyRest(key=test_vars["keys"][0]["key_str"], use_token_auth=True)

        self.assertTrue(ably.auth.auth_options.use_token_auth)

    def test_query_time_can_be_enabled(self):
        ably = AblyRest(key=test_vars["keys"][0]["key_str"], query_time=True)

        self.assertTrue(ably.auth.auth_options.query_time)

    def test_auth_token_details(self):
        ably = AblyRest(token='this_is_not_really_a_token')

        self.assertIsInstance(ably.auth.token_details, TokenDetails,
                              msg="Token details is None.")

    def test_auth_init_with_auth_headers(self):
        ably = AblyRest(key=test_vars["keys"][0]["key_str"], 
                        auth_headers='this_is_not_really_a_header')

        self.assertEqual(ably.auth.auth_options.auth_headers,
                         'this_is_not_really_a_header')

    def test_auth_init_with_auth_params(self):
        ably = AblyRest(key=test_vars["keys"][0]["key_str"],
                        auth_params="this_is_not_really_a_auth_params")

        self.assertEqual(ably.auth.auth_options.auth_params,
                         'this_is_not_really_a_auth_params')
