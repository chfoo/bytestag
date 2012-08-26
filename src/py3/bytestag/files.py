'''File manipulation'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
import contextlib
import os
import platform
import shutil

__docformat__ = 'restructuredtext en'


@contextlib.contextmanager
def file_overwriter(path, flags='wb'):
    new_temp_path = '{}-new~'.format(path)
    old_temp_path = '{}~'.format(path)

    with open(new_temp_path, flags) as f:
        yield f

    if os.path.exists(path):
        shutil.copy(path, old_temp_path)

    if platform.system() == 'Windows' and os.path.exists(path):
        os.remove(path)

    os.rename(new_temp_path, path)
