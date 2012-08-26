# cx_freeze script for Windows and MacOS
# See README for more info!

import sys
import os
from cx_Freeze import setup, Executable

src_dir = os.path.abspath(os.path.join('src', 'py3'))
sys.path.insert(0, src_dir)

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "build_exe": {
        "includes" : ["atexit", 
            'PySide.QtCore',
            'PySide.QtGui', 
            'PySide.QtUiTools', 
            'PySide.QtXml', # Installs DLL needed for PySide.QtUiTools
        ],
        'include_files': [
            ('src/py3/bytestagui/qt/views/ui/', 'bytestagui/qt/views/ui/'),
        ],
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

setup(
    name="Bytestag",
    version="0.0.0",
    description="Bytestag Peer-To-Peer File Sharing Client",
    options=build_exe_options,
    author='Christopher Foo',
    executables=[
        Executable("src/py3/bytestagui/main_qt.py", base=base,
            targetName='bytestag.exe',
        )
    ],
)
