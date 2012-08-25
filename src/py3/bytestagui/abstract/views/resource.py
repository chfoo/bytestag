'''Resource access'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
import abc


class Resource(metaclass=abc.ABCMeta):
    @abc.abstractclassmethod
    def get_bytes(self, name):
        pass
