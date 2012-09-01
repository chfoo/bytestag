'''Base classes'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
import abc
import collections

__docformat__ = 'restructuredtext en'


class ControllerSingletons(collections.MutableMapping):
    def __init__(self,):
        self._str_map = {}
        self._class_map = {}

    def __getitem__(self, o):
        if isinstance(o, str):
            return self._str_map[o]

        return self._class_map[o]

    def __setitem__(self, class_, instance):
        self._class_map[class_] = instance

        assert class_.__name__ not in self._str_map

        self._str_map[class_.__name__] = instance

    def __delitem__(self, o):
        if isinstance(o, str):
            del self._class_map[self._str_map[o].__class__]
            del self._str_map[o]
        else:
            del self._str_map[o.__name__]
            del self._class_map[o]

    def __iter__(self):
        for class_ in self._class_map:
            yield class_

    def __len__(self):
        return len(self._class_map)


class BaseApplication(metaclass=abc.ABCMeta):
    '''Base application.'''

    def __init__(self):
        self._singletons = ControllerSingletons()

    @property
    def singletons(self):
        return self._singletons

    def new_singleton(self, class_):
        assert class_ not in self._singletons

        instance = class_(self)
        self._singletons[class_] = instance

        return instance

    @abc.abstractmethod
    def run(self):
        pass

    @abc.abstractmethod
    def stop(self):
        pass


class BaseController(object):
    '''Base controller.'''

    def __init__(self, application):
        self._application = application

    @property
    def application(self):
        '''The application'''
        return self._application
