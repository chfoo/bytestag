'''Shared files screen'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from bytestagui.abstract.controllers.base import BaseController


class SharedFilesController(BaseController):
    def __init__(self, application):
        BaseController.__init__(self, application)
        self._shared_directories = self.application.singletons[
            'DHTClientController'].client.shared_files_table.shared_directories

        self._shared_directories.extend(self._get_shared_dirs_from_config())

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

        for i in range(len(self._shared_directories)):
            directory = self._shared_directories[i]

            config_parser['shared_files']['path{}'.format(i)] = directory

        self.application.singletons['ConfigController'].save()

