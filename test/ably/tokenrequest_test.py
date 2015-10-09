from __future__ import unicode_literals

import json
import unittest

from six import text_type

from ably.types.capability import Capability
from ably.types.tokenrequest import TokenRequest


class TestTokenRequest(unittest.TestCase):

    def setUp(self):
        self.capability_dict = {'value': 'abcd'}
        self.attrs = {
            'capability': Capability(self.capability_dict),
            'key_name':  'key_name',
            'ttl': 1000,
            'client_id': 'client_id',
            'nonce': 'a_nonce',
            'mac': 'a_mac',
        }
        self.token_request = TokenRequest(self.attrs)

    def test_string_attrs(self):
        tr = self.token_request
        self.assertIsInstance(tr.key_name, text_type)
        self.assertIsInstance(tr.client_id, text_type)
        self.assertIsInstance(tr.nonce, text_type)
        self.assertIsInstance(tr.mac, text_type)
        self.assertIsInstance(tr.capability, text_type)

    def test_int_attrs(self):
        tr = self.token_request
        self.assertIsInstance(tr.ttl, int)

    def test_request(self):
        self.assertTrue(self.token_request.hash)
        self.assertIsInstance(self.token_request.hash, dict)
