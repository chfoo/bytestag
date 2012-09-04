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


BAD_CHARS = '{}{}\x00'.format(os.sep, os.altsep or os.sep)
WINDOWS_BAD_CHARS = '{}{}"*:<>?|\\'.format(BAD_CHARS,
    ''.join([chr(i) for i in range(1, 32)])
)

BAD_CHAR_TABLE = str.maketrans(BAD_CHARS, '_' * len(BAD_CHARS))
WINDOWS_BAD_CHAR_TABLE = str.maketrans(WINDOWS_BAD_CHARS,
    '_' * len(WINDOWS_BAD_CHARS))


BAD_WINDOWS_FILENAMES = frozenset(['CON', 'PRN', 'AUX', 'NUL', 'CLOCK$']
    + ['COM{}'.format(i) for i in range(1, 10)]
    + ['LPT{}'.format(i) for i in range(1, 10)])


def safe_filename(filename, os_name=platform.system()):
    if os_name.startswith('Windows'):
        table = WINDOWS_BAD_CHAR_TABLE
    else:
        table = BAD_CHAR_TABLE

    filename = filename.translate(table)

    if os_name.startswith('Windows'):
        filename = filename.rstrip()

        if filename.endswith('.'):
            raise ValueError('Unsafe filename: ends with fullstop')

        if os.path.splitext(filename)[0] in BAD_WINDOWS_FILENAMES:
            raise ValueError('Unsafe filename: Windows reserved filename')

    if filename == os.pardir:
        raise ValueError('Unsafe filename: parent directory')

    return filename
