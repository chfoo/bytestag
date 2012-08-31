'''UI file inflater'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from bytestagui.base.controllers.app import BaseController
import abc


class BaseInflaterController(BaseController, metaclass=abc.ABCMeta):
    def __init__(self, application):
        BaseController.__init__(self, application)

