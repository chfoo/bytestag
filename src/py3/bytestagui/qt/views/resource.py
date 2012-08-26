import bytestagui.abstract.views.resource
import bytestagui.qt.views
import os.path
import pkg_resources


class Resource(bytestagui.abstract.views.resource.Resource):
    @classmethod
    def get_bytes(cls, name):
        try:
            return pkg_resources.resource_string(bytestagui.qt.views.__name__,
                name)
        except IOError:
            return Resource.get_bytes_fallback(name)

    @classmethod
    def get_fallback_path(cls, name):
        return os.path.join(os.getcwd(), 'bytestagui', 'qt', 'views',
            *name.split('/'))

    @classmethod
    def get_bytes_fallback(cls, name):
        with open(Resource.get_fallback_path(name), 'rb') as f:
            return f.read()

