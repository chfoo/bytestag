import bytestagui.abstract.views.resource
import bytestagui.gtk.views
import pkg_resources


class Resource(bytestagui.abstract.views.resource.Resource):
    @classmethod
    def get_bytes(cls, name):
        return pkg_resources.resource_string(bytestagui.gtk.views.__name__,
            name)
