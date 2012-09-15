Intro
========

Bytestag: Wide Availability Peer-to-Peer File Sharing

Bytestag is a peer-to-peer (P2P) file sharing system that uses a distributed
hash table (DHT) to achieve wide availability of files. Unlike the BitTorrent
protocol, files are published entirely via DHT and do not require trackers
or swarming. Each computer donates disk space and bandwidth for caching of
published values.

This software is currently under development.

..  The above summary is from bytestag.__init__.py. 
    Be sure to edit this file as well.

Installation
============

Pre-Built Packages
++++++++++++++++++

Please check `the wiki <https://github.com/chfoo/bytestag/wiki/>`_ for the
latest information about packages.

From Source
+++++++++++

Dependencies
------------

You will need:

1. Python >=3.2
2. Python module bitstring >=3.0
3. Python module miniupnpc >= 1.7.20120830

If you want the GUI you will need:

1. PySide (for Python 3)
2. Qt

Install
-------

Run the commands::

    python3 setup.py build
    python3 setup.py install

Run
---

The command line version can be run as::

    python3 -m bytestag

The GUI version can be run as::

    python3 -m bytestagui

With cx_freeze (Windows, MacOS)
+++++++++++++++++++++++++++++++

Dependencies
------------

1. Python >= 3.2
2. PySide which should match the Python version and whether it is
   32 or 64 bit.
3. cx_freeze (which, again, should match the Python version you
   installed.)
4. If Windows, pywin32 extensions (matching Python version and 32/64 bit)
5. The Python module miniupnpc >= 1.7.20120830.


Build and Freeze
----------------

1. Run the command in project directory
   ``python setup_cx_freeze.py build``. If you are using Windows,
   I suggest using the Power Shell.
2. Change directory into ``build/XXXXX`` and test running the executable.
3. Change back to the project directory and run the command
   ``python setup_cx_freeze.py bdist_msi`` or
   ``python setup_cx_freeze.py bdist_dmg``
   to generate the installers or disk images.

For Windows, Microsoft Visual C++ 2008 Redistributable Package is needed.
SP1 is not needed. Be sure to match 32 or 64 bit. 
Read the cx_freeze documentation for details.

If it crashes hard on Windows, install the Windows Debugger Tools (WinDbg) 
to attach to the process and see which module failed to import. 
It is usually a missing DLL.

miniupnpc
+++++++++

Miniupnpc can be obtained from `<http://miniupnp.free.fr/>`_. The build
targets needed are ``init``, ``libminiupnpc.a``, ``pythonmodule3``, and
``installpythonmodule3``.

To build and install using Mingw32, use commands similar to::

    mingw32-make -f Makefile.mingw -C init libminiupnpc.a pythonmodule
    
Fine-control over python install::

    python.exe setupmingw32.py build --compiler mingw32
    python.exe setupmingw32.py install --prefix PREFIX_HERE

Contributing
============

The project page is located at `<https://launchpad.net/bytestag>`_. Code,
bug reports, translations, and questions are welcomed there.

The code is occasionally mirrored at `<https://github.com/chfoo/bytestag>`_.

Project directory structure
+++++++++++++++++++++++++++

A suggested local project directory structure is as follows::

    bytestag/bytestag.bzr/trunk/
    bytestag/bytestag.bzr/unstable/
    bytestag/bytestag.bzr/stable/
    bytestag/bytestag.bzr/branches/bug-NNNNN/
    bytestag/bytestag.bzr/branches/feature-XXXXX/

``bytestag.bzr`` is a Bzr shared repository. It is usually created by
executing ``bzr init-repo --no-trees bytestag.bzr`` in the ``bytestag``
directory.

You might not want to work with Bzr, so use you can put a repo next to it::

    bytestag/bytestag.git/

For more structure/layout ideas, see 
`<http://wiki.bazaar.canonical.com/SharedRepositoryLayouts>`_.


Tags
++++

Release tags for any version (alpha, beta, etc.) should use
``vN.N[.N]+[{a|b|c|rc}N[.N]+]``. For example: ``v1.2b1``.


Documentation
=============

The documentation is located in the doc directory. Sphinx is used to generate
the documents. They can be read at `<http://packages.python.org/Bytestag/>`_.

Please update the release notes in the doc directory for releases.

Packaging
=========

Packaging scripts and templates are included in the pkg directory. 
If packaging templates do not work, require unnecessary tweaking, 
or violate packaging policies, please tell us.


