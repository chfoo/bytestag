'''DHT downloader

This module includes classes help download files and collections.
'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from bytestag.storage import SQLite3Mixin
from bytestag.events import EventReactorMixin


class Downloader(EventReactorMixin, SQLite3Mixin):
    def __init__(self, event_reactor, config_dir, dht_network, download_slot):
        EventReactorMixin.__init__(self, event_reactor)
