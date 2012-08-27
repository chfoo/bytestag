'''Resources'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
import bytestagui.abstract.views.resource
import bytestagui.gtk.views
import bytestag.lib.pkg_resources


class Resource(bytestagui.abstract.views.resource.Resource):
    @classmethod
    def get_bytes(cls, name):
        return bytestag.lib.pkg_resources.resource_string(
            bytestagui.gtk.views.__name__, name)
