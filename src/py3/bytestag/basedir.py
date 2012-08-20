'''Quick and dirty platform specific base directories.

On Unix environments, XDG environment variables are used. On Windows,
the environment variable ``%LOCALAPPDATA%`` is used for building paths.
If neither, variables exist, the home directory variable is used. If
the home variable does not exist. It uses the current directory and returns
a directory in the style of ``.NAMESPACE``.

:var cache_dir: A directory suitable for storing files that you don't mind
    losing but wish to keep around for a while.

    One of the following:

    1. ``$XDG_CACHE_HOME/NAMESPACE/``
    2. ``%LOCALAPPDATA%/NAMESPACE/cache/``
    3. ``~/.cache/NAMESPACE``
    4. ``./.NAMESPACE/cache/``

:var data_dir: A directory suitable for storing program code or plugins.

    One of the following:

    1. ``$XDG_DATA_HOME/NAMESPACE/``
    2. ``%LOCALAPPDATA%/NAMESPACE/data/``
    3. ``~/.share/NAMESPACE``
    4. ``./.NAMESPACE/data/``

:var config_dir: A directory suitable for storing program configurations.

    One of the following:

    1. ``$XDG_CONFIG_HOME/NAMESPACE/``
    2. ``%LOCALAPPDATA%/NAMESPACE/config/``
    3. ``~/.config/NAMESPACE``
    4. ``./.NAMESPACE/config/``

:var runtime_dir: A directory suitable for storing program runtime files
    such as Unix sockets, PID files, or named pipes.

    One of the following:

    1. ``$XDG_RUNTIME_DIR/NAMESPACE/``
    2. ``$TEMP/NAMESPACE/`` (via :func:`tempfile.gettempdir`)
'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
import os
import tempfile

__docformat__ = 'restructuredtext en'
NAMESPACE = 'bytestag'


def _get_dir(xdg, windows, fallback, namespace=NAMESPACE):
    if xdg in os.environ:
        return os.path.join(os.environ[xdg], namespace)

    if 'LOCALAPPDATA' in os.environ:
        return os.path.join(os.environ['LOCALAPPDATA'], namespace, windows)

    path = os.path.join(os.path.expanduser('~'), fallback, namespace)

    if path.startswith('~'):
        return os.path.join('.{}'.format(namespace, windows))
    else:
        return path


def _get_dir_simple(xdg):
    if xdg in os.environ:
        return os.path.join(os.environ[xdg], NAMESPACE)

    return os.path.join(tempfile.gettempdir(), NAMESPACE)


# TODO: this should be using CSIDL_INTERNET_CACHE instead
cache_dir = _get_dir('XDG_CACHE_HOME', 'cache', '.cache')
data_dir = _get_dir('XDG_DATA_HOME', 'data', '.share')
config_dir = _get_dir('XDG_CONFIG_HOME', 'config', '.config')
runtime_dir = _get_dir_simple('XDG_RUNTIME_DIR')
