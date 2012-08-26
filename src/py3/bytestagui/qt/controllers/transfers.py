'''Transfer screen'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from bytestagui.abstract.controllers.base import BaseController


class TransfersTabController(BaseController):
    def __init__(self, application):
        BaseController.__init__(self, application)