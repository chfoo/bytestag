from bytestag import basedir
from bytestag.files import file_overwriter
from bytestag.keys import KeyBytes
from bytestagui.controllers.base import BaseController
from collections import OrderedDict
import configparser
import os.path


class ConfigController(BaseController):
    def __init__(self, application):
        BaseController.__init__(self, application)
        config_parser = configparser.ConfigParser()
        config_parser.read_dict(OrderedDict([
            ('network', OrderedDict([
                ('host', '0.0.0.0'),
                ('port', 0),
                ('node_id', KeyBytes().base64),
            ])),
            ('known_nodes', OrderedDict([
                ('host1', 'localhost'),
                ('port1', 12345),
            ])),
            ('shared_files', OrderedDict([
            ])),
        ]))

        filename = os.path.join(basedir.config_dir, 'bytestag.conf')
        config_parser.read([filename])

        self._config_parser = config_parser
        self._filename = filename

    @property
    def config_parser(self):
        return self._config_parser

    def save(self):
        os.makedirs(os.path.dirname(self._filename), mode=0o777, exist_ok=True)

        with file_overwriter(self._filename, flags='w') as f:
            self._config_parser.write(f)
