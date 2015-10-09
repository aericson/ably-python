from __future__ import absolute_import

from six import text_type


class TokenRequest(object):

    def __init__(self, attributes={}):
        self.__hash = dict(attributes)

    @property
    def hash(self):
        return self.__hash

    @property
    def key_name(self):
        return self.hash['key_name']

    @property
    def ttl(self):
        return self.hash['ttl']

    @property
    def capability(self):
        return text_type(self.hash['capability'])

    @property
    def client_id(self):
        return self.hash['client_id']

    @property
    def nonce(self):
        return self.hash['nonce']

    @property
    def mac(self):
        return self.hash['mac']
