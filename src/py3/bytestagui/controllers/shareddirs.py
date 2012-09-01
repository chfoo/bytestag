'''Shared directories'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from bytestagui.controllers.base import BaseController
from bytestagui.controllers.config import ConfigController
from bytestagui.controllers.dht import DHTClientController


class SharedDirsController(BaseController):
    '''Provides access to ``shared_files`` config section'''

    def __init__(self, application):
        BaseController.__init__(self, application)

        self._client_shared_directories = self.application.singletons[
            DHTClientController].client.shared_files_table.shared_directories
        self._shared_directories = set()

        config = self.application.singletons[ConfigController]
        config.observer.register(self._config_changed_cb)

        for d in self._get_shared_dirs_from_config():
            self._shared_directories.add(d)

        self._populate_client_table()

    def _config_changed_cb(self, section, option, value):
        if section == 'sharing' and option == 'default_share_dir':
            self._populate_client_table()

    def _get_shared_dirs_from_config(self):
        config_parser = self.application.singletons['ConfigController'
            ].config_parser

        l = []

        for key in config_parser['shared_files'].keys():
            l.append(config_parser['shared_files'][key])

        return l

    def _save_shared_files_config(self):
        config_parser = self.application.singletons['ConfigController'
            ].config_parser

        config_parser['shared_files'] = {}

        i = 0

        for directory in self._shared_directories:
            config_parser['shared_files']['path{}'.format(i + 1)] = directory

            i += 1

        self.application.singletons['ConfigController'].save()

    @property
    def _default_share_dir(self):
        config_parser = self.application.singletons['ConfigController'
            ].config_parser

        return config_parser['sharing']['default_share_dir']

    def add_directory(self, *directory):
        for d in directory:
            self._shared_directories.add(d)

        self._save_shared_files_config()
        self._populate_client_table()

    def remove_directory(self, *directory):
        for d in directory:
            self._shared_directories.remove(d)

        self._save_shared_files_config()
        self._populate_client_table()

    def _populate_client_table(self):
        del self._client_shared_directories[:]

        self._client_shared_directories.append(self._default_share_dir)
        self._client_shared_directories.extend(tuple(self._shared_directories))

    @property
    def shared_directories(self):
        return self._shared_directories
