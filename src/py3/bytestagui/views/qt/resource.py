'''Resources'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
import bytestag.lib.pkg_resources
from bytestagui.views.resource import Resource as BaseResource
import bytestagui.views.qt
import os.path
import sys


class Resource(BaseResource):
    @classmethod
    def get_bytes(cls, name):
        try:
            return bytestag.lib.pkg_resources.resource_string(
                bytestagui.views.qt.__name__, name)
        except IOError:
            return Resource.get_bytes_fallback(name)

    # TODO: push these methods up into abstract
    @classmethod
    def get_fallback_path(cls, name):
        appdir = os.path.dirname(sys.argv[0])
        return os.path.join(appdir, 'bytestagui', 'qt', 'views',
            *name.split('/'))

    @classmethod
    def get_bytes_fallback(cls, name):
        with open(Resource.get_fallback_path(name), 'rb') as f:
            return f.read()

