'''Resources'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from bytestagui.base.views.resource import Resource as BaseResource
import bytestag.lib.pkg_resources
import bytestagui.gtk.views


class Resource(BaseResource):
    @classmethod
    def get_bytes(cls, name):
        return bytestag.lib.pkg_resources.resource_string(
            bytestagui.gtk.views.__name__, name)
