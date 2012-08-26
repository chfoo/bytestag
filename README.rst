Intro
========

Bytestag: Wide Availability Peer-to-Peer File Sharing

Bytestag is a peer-to-peer (P2P) file sharing system that uses a distributed
hash table (DHT) to achieve wide availability of files. Unlike the BitTorrent
protocol, files are published entirely via DHT and do not require trackers
or swarming. Each computer donates disk space and bandwidth for caching of
published values.

This software is currently under development.

Installation
============

Pre-Built Packages
++++++++++++++++++

Pre-built packages are not ready yet.

From Source
+++++++++++

Dependencies
------------

You will need:

1. Python >=3.2
2. Python module bitstring >=3.0

If you want the GUI (for GNU/Linux), you will also need:

1. PyGObject >=3.0 (which should include gobject-introspection)
2. GTK+3

If you want the GUI (for Windows, MacOS, etc.), you will need:

1. PySide
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
`<http://wiki.bazaar.canonical.com/SharedRepositoryLayouts`>_.


Tags
++++

Release tags for any version (alpha, beta, etc.) should use
``vN.N[.N]+[{a|b|c|rc}N[.N]+]``. For example: ``v1.2b``.


Documentation
=============

The documentation is located in the doc directory. Sphinx is used to generate
the documents.
They will be made available online as well at 
`<http://packages.python.org/Bytestag>`_ or possibly at readthedocs.org.

Packaging
=========

Packaging scripts and templates are included in the pkg directory. 
If packaging templates do not work, require unnecessary tweaking, 
or violate packaging policies, please tell us.


