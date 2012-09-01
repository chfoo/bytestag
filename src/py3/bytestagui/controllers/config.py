'''Configuration management'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from bytestag import basedir
from bytestag.events import Observer
from bytestag.files import file_overwriter
from bytestag.keys import KeyBytes
from bytestagui.controllers.base import BaseController
from collections import OrderedDict
import configparser
import logging
import os.path
import random
import uuid


_logger = logging.getLogger(__name__)


class ConfigController(BaseController):
    '''Provides access to :class:`.ConfigParser`'''

    def __init__(self, application):
        BaseController.__init__(self, application)

        config_parser = configparser.ConfigParser()
        default_share_dir = os.path.expanduser(os.path.join('~', 'Bytestag'))

        host_random = random.Random(uuid.getnode())

        self.defaults = defaults = OrderedDict([
            ('network', OrderedDict([
                ('host', '0.0.0.0'),
                ('port', host_random.randint(1024, 2 ** 16 - 1)),
                ('node_id', KeyBytes().base64),
            ])),
            ('known_nodes', OrderedDict([
                ('host1', 'torwuf.com'),
                ('port1', 38664),
            ])),
            ('shared_files', OrderedDict([
            ])),
            ('sharing', OrderedDict([
                ('default_share_dir', default_share_dir),
            ])),
            ('cache', OrderedDict([
                ('max_size', 17179869184),
            ])),
        ])

        config_parser.read_dict(defaults)

        filename = os.path.join(basedir.config_dir, 'bytestag.conf')
        config_parser.read([filename])

        self._config_parser = config_parser
        self._filename = filename
        self._observer = Observer()

    @property
    def config_parser(self):
        return self._config_parser

    @property
    def observer(self):
        return self._observer

    def save(self):
        os.makedirs(os.path.dirname(self._filename), mode=0o777, exist_ok=True)

        with file_overwriter(self._filename, flags='w') as f:
            self._config_parser.write(f)

    def set(self, section, option, value):
        assert isinstance(value, (str, int, float, bool))

        self._config_parser[section][option] = str(value)

        self._observer(section, option, value)

    def get(self, section, option, as_bool=False):
        if as_bool:
            return self._config_parser.getboolean(section, option)

        return self._config_parser[section][option]

    def set_default(self, section, option):
        self.set(section, option, self.defaults[section][option])
