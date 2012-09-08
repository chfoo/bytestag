'''Resources'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
import bytestagui.views.resource
import bytestagui.views.qt


class QTResource(bytestagui.views.resource.Resource):
    module_name = bytestagui.views.qt.__name__
