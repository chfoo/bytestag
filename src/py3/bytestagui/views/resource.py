'''Resource access'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
import bytestag.lib.pkg_resources
import bytestagui.views
import logging
import os.path
import sys

_logger = logging.getLogger(__name__)


class Resource(object):
    module_name = bytestagui.views.__name__

    @classmethod
    def get_bytes(cls, name):
        try:
            return bytestag.lib.pkg_resources.resource_string(
                cls.module_name, name)
        except IOError:
            return cls.get_bytes_fallback(name)

    @classmethod
    def get_fallback_path(cls, name):
        appdir = os.path.dirname(sys.argv[0])

        if os.path.exists(os.path.join(appdir, 'views')):
            module_path = cls.module_name.split('.')[1:]
        else:
            module_path = cls.module_name.split('.')

        path = os.path.join(os.path.join(appdir, *module_path),
            *name.split('/'))

        if not os.path.exists(path):
            _logger.warning('Resource path %s doesnt exist', path)

        return path

    @classmethod
    def get_bytes_fallback(cls, name):
        with open(cls.get_fallback_path(name), 'rb') as f:
            return f.read()
