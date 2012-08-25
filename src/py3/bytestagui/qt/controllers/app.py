'''Application'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from bytestagui.abstract.controllers.config import ConfigController
from bytestagui.qt.controllers.loader import LoaderController
import bytestagui.abstract.controllers.app


class Application(bytestagui.abstract.controllers.app.Application):
    def __ini__(self):
        bytestagui.abstract.controllers.app.Application.__init__(self)
        self.new_singleton(LoaderController)
        self.new_singleton(ConfigController)

    def run(self):
        pass

    def stop(self):
        pass
