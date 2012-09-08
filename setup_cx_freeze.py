# cx_freeze script for Windows and MacOS
# See README for more info!

import sys
import os
from cx_Freeze import setup, Executable
import glob
import distutils.version
import posixpath

src_dir = os.path.abspath(os.path.join('src', 'py3'))
sys.path.insert(0, src_dir)
import bytestagui

import PySide

pyside_dir = os.path.dirname(PySide.__file__)

def glob_include(pattern, dest_prefix):
    for path in glob.glob(pattern):
        path = path.replace(os.sep, '/')
        
        return path, '{}/{}'.format(dest_prefix, posixpath.basename(path))


# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "build_exe": {
        "includes" : ["atexit", 
            'PySide.QtCore',
            'PySide.QtGui', 
            'PySide.QtUiTools', 
            'PySide.QtXml',  # Installs DLL needed for PySide.QtUiTools
            'PySide.QtSvg',  # For svg window icon
            'bytestag.lib._bitstring',
            'bytestag.lib._pkg_resources',
        ],
        'include_files': [
            ('src/py3/bytestagui/views/qt/ui/', 'bytestagui/views/qt/ui/'),
            ('src/py3/bytestagui/views/img/', 'bytestagui/views/img/'),
            ('pkg/qt.conf', 'qt.conf'),
            glob_include(os.path.join(pyside_dir, 'plugins', 'iconengines', 
                'qsvgicon*'), 'plugins/iconengines/'),
#            glob_include(os.path.join(pyside_dir, 'plugins', 'imageformats', 
#                'qsvg*'), 'plugins/imageformats/'),
        ],
        'icon': 'img/logo/bytestag_app.ico',
    },
    "bdist_dmg": {
        'volume-label': 'Bytestag',
    },
}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

numerical_version = distutils.version.StrictVersion(bytestagui.__version__
    ).version

setup(
    name="Bytestag",
    version='.'.join(map(str, numerical_version)),
    description="Bytestag Peer-To-Peer File Sharing Client",
    options=build_exe_options,
    author='Christopher Foo',
    executables=[
        Executable("src/py3/bytestagui/main_qt.py", base=base,
            targetName='bytestag.exe',
            shortcutName='Bytestag',
            shortcutDir='ProgramMenuFolder',
        )
    ],
)
