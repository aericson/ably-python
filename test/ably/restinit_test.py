from __future__ import absolute_import

import unittest

from ably import AblyRest
from ably import AblyException
from ably.transport.defaults import Defaults

from test.ably.restsetup import RestSetup

test_vars = RestSetup.get_test_vars()


class TestRestInit(unittest.TestCase):
    def test_key_only(self):
        ably = AblyRest(key=test_vars["keys"][0]["key_str"])
        self.assertEqual(ably.options.key_name, test_vars["keys"][0]["key_name"],
                         "Key name does not match")
        self.assertEqual(ably.options.key_secret, test_vars["keys"][0]["key_secret"],
                         "Key secret does not match")

    def test_with_token(self):
        ably = AblyRest(token="foo")
        self.assertEqual(ably.options.auth_token, "foo",
                         "Token not set at options")

    def test_client_id(self):
        ably = AblyRest(token="foo", client_id="bar")
        self.assertEqual(ably.options.client_id, "bar",
                         "Client ID does not match")

    def test_with_options_token_callback(self):
        def token_callback(**params):
            return "this_is_not_really_a_token_request"
        AblyRest(auth_callback=token_callback)

    def test_ambiguous_key_raises_value_error(self):
        self.assertRaisesRegexp(ValueError, "mutually exclusive", AblyRest,
                                key=test_vars["keys"][0]["key_str"],
                                key_name='x')
        self.assertRaisesRegexp(ValueError, "mutually exclusive", AblyRest,
                                key=test_vars["keys"][0]["key_str"],
                                key_secret='x')

    def test_with_key_name_or_secret_only(self):
        self.assertRaisesRegexp(ValueError, "key is missing", AblyRest,
                                key_name='x')
        self.assertRaisesRegexp(ValueError, "key is missing", AblyRest,
                                key_secret='x')

    def test_with_key_name_and_secret(self):
        ably = AblyRest(key_name="foo", key_secret="bar")
        self.assertEqual(ably.options.key_name, "foo",
                         "Key name does not match")
        self.assertEqual(ably.options.key_secret, "bar",
                         "Key secret does not match")

    def test_with_options_auth_url(self):
        AblyRest(auth_url='not_really_an_url')

    def test_specified_host(self):
        ably = AblyRest(token='foo', host="some.other.host")
        self.assertEqual("some.other.host", ably.options.host,
                         msg="Unexpected host mismatch")

    def test_specified_port(self):
        ably = AblyRest(token='foo', port=9998, tls_port=9999)
        self.assertEqual(9999, Defaults.get_port(ably.options),
                         msg="Unexpected port mismatch. Expected: 9999. Actual: %d" %
                         ably.options.tls_port)

    def test_log_level_defaults_to_zero(self):
        ably = AblyRest(token='foo')
        self.assertEqual(ably.options.log_level, 0)

    def test_log_level_can_be_changed(self):
        ably = AblyRest(token='foo', log_level=1)
        self.assertEqual(ably.options.log_level, 1)

    def test_tls_defaults_to_true(self):
        ably = AblyRest(token='foo')
        self.assertTrue(ably.options.tls,
                        msg="Expected encryption to default to true")
        self.assertEqual(Defaults.tls_port, Defaults.get_port(ably.options),
                         msg="Unexpected port mismatch")

    def test_tls_can_be_disabled(self):
        ably = AblyRest(token='foo', tls=False)
        self.assertFalse(ably.options.tls,
                         msg="Expected encryption to be False")
        self.assertEqual(Defaults.port, Defaults.get_port(ably.options),
                         msg="Unexpected port mismatch")

    def test_use_binary_protocol_defaults_to_true(self):
        ably = AblyRest(token='foo')
        self.assertTrue(ably.options.use_binary_protocol)

    def test_use_binary_protocol_can_be_disabled(self):
        ably = AblyRest(token='foo', use_binary_protocol=False)
        self.assertFalse(ably.options.use_binary_protocol)

    def test_with_no_params(self):
        self.assertRaises(ValueError, AblyRest)

    def test_with_no_auth_params(self):
        self.assertRaises(ValueError, AblyRest, port=111)


if __name__ == "__main__":
    unittest.main()
