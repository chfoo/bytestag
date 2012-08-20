
#
#
#
#class ValueDownloader(threading.Thread):
#    '''Downloads a single value from a select set of nodes'''
#
#    def __init__(self, controller, key, index):
#        threading.Thread.__init__(self)
#        self.daemon = True
#        self.name = 'downloader-{}'.format(key.base32)
#        self._controller = controller
#        self._key = key
#        self._index = index
#        self._file = tempfile.SpooledTemporaryFile(max_size=1048576)
#        self._bytes_read = 0
#        self._total_size = 0
#        self._observer = Observer()
#        self._running = True
#        self._finished = False
#        self._current_progress = None
#
#    @property
#    def observer(self):
#        '''Returns the observer which will be called when finished
#
#        :rtype: `Observer`
#        '''
#
#        return self._observer
#
#    @property
#    def finished(self):
#        '''Returns whether the download attempt was finished.
#
#        A finished status does not mean that the download was successful.
#        '''
#        return self._finished
#
#    @property
#    def file(self):
#        '''Returns the file object'''
#
#        return self._file
#
#    @property
#    def bytes_read(self):
#        '''Returns the number of bytes read'''
#
#        return self._bytes_read
#
#    def run(self):
#        self._download_append()
#
#        self._finished = True
#        self._observer()
#
#    def validate_file(self, hash_bytes):
#        '''Validate the sha1'''
#
#        self._file.seek(0)
#
#        hasher = hashlib.sha1()
#
#        while True:
#            data = self._file.read(10240)
#
#            if not data:
#                break
#
#            hasher.update(data)
#
#        return hash_bytes == hasher.digest()
#
#    def stop(self):
#        '''Stop download'''
#
#        self._running = False
#
#        if self._current_progress:
#            self._current_progress.stop()
#
#    def _download_append(self, iteration_attempts=3):
#        future = self._controller.find_value_shortlist(self._key, self._index)
#        shortlist = future.result()
#
#        useful_node_list = NodeList(shortlist.useful_nodes)
#        useful_node_list.sort_distance(self._key)
#
#        for i in range(iteration_attempts):
#            _logger.debug('Download append iteration=%d', i)
#
#            self._download_append_from_list(useful_node_list,
#                shortlist.most_common_data_size)
#
#            if self._bytes_read >= shortlist.most_common_data_size:
#                return True
#
#    def _download_append_from_list(self, node_list, max_size):
#        for node in node_list:
#            self._download_append_from_node(node)
#
#            if self._bytes_read >= max_size:
#                break
#
#    def _download_append_from_node(self, node):
#        _logger.debug('Download append from node %s', node)
#
#        progress = self._controller.get_value_from_node(node, self._key,
#                offset=self._bytes_read)
#        self._current_progress = progress
#        f = progress.result()
#
#        if not self._running:
#            return
#
#        f.seek(0, 2)
#        bytes_read = f.tell()
#        f.seek(0)
#
#        self._bytes_read += bytes_read
#
#        _logger.debug('Received %d bytes', bytes_read)
#        shutil.copyfileobj(f, self._file)
#
#
#class MultiValueDownloader(threading.Thread):
#    '''Downloads mulitple values from a select set of nodes'''
#
#    def __init__(self, controller, key):
#        threading.Thread.__init__(self)
#        self.daemon = True
#        self.name = 'multidownloader-{}'.format(key.base32)
#        self._controller = controller
#        self._key = key
#        self._observer = Observer()
#        self._downloaders = []
#
#    @property
#    def observer(self):
#        '''Returns the observer which will be called when finished
#
#        :rtype: `Observer`
#        '''
#
#        return self._observer
#
#    @property
#    def finished(self):
#        '''Returns whether the download attempt was finished.
#
#        A finished status does not mean that the download was successful.
#        '''
#        return all([d.finished for d in self._downloaders])
#
#    def run(self):
#        future = self._controller.find_multi_value(self._key)
#        shortlist = future.result()
#
#
#
#        self._observer()
