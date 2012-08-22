'''Base classes'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.

__docformat__ = 'restructuredtext en'


class BaseApplication(object):
    '''Base application.'''

    def __init__(self):
        self._singletons = {}

    @property
    def singletons(self):
        return self._singletons

    def new_singleton(self, class_):
        assert class_ not in self._singletons

        instance = class_(self)
        self._singletons[class_] = instance

        return instance


class BaseController(object):
    '''Base controller.'''

    def __init__(self, application):
        self._application = application

    @property
    def application(self):
        '''The application'''
        return self._application
