'''Application'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from bytestagui.abstract.controllers.base import BaseApplication
import abc


class Application(BaseApplication, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def run(self):
        pass

    @abc.abstractmethod
    def stop(self):
        pass
