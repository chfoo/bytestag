import bytestagui.abstract.views.resource
import pkg_resources
import bytestagui.qt.views


class Resource(bytestagui.abstract.views.resource.Resource):
    @classmethod
    def get_bytes(cls, name):
        return pkg_resources.resource_string(bytestagui.qt.views.__name__,
            name)
