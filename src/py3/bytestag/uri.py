'''Bytestag URIs'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from bytestag.keys import KeyBytes
import collections
import urllib.parse


class MagnetURI(object):
    def __init__(self):
        self._params = collections.defaultdict(list)

    @classmethod
    def parse(cls, s):
        uri = MagnetURI()

        if not s.lower().startswith('magnet:'):
            raise ValueError('scheme is not magnet')

        query_str = s.split('?', 1)[1]
        query_dict = urllib.parse.parse_qs(query_str)

        for key in query_dict:
            if '.' in key:
                param_key = key.split('.', 1)[0]

                uri.params[param_key].extend(query_dict[key])
            else:
                uri.params[key].extend(query_dict[key])

        return uri

    @property
    def params(self):
        return self._params

    def get_first_param(self, key, default=None):
        if self._params[key]:
            return self._params[key][0]

        return default

    @property
    def exact_topic(self):
        if self._params['xt']:
            return self._params['xt'][0]

    @property
    def bittorent_info_hash(self):
        exact_topic = self.exact_topic

        if exact_topic and exact_topic.startswith('urn:btih:'):
            return KeyBytes(exact_topic[9:])

    @property
    def bytestag_info_hash(self):
        exact_topic = self.exact_topic

        if exact_topic and exact_topic.startswith('urn:bstagih:'):
            return KeyBytes(exact_topic[12:])

    @bytestag_info_hash.setter
    def bytestag_info_hash(self, key_bytes):
        del self._params['xt'][:]

        self._params['xt'].append('urn:bstagih:{}'.format(key_bytes.base32))
