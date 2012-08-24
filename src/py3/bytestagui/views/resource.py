import bytestagui.views
import pkg_resources


def get_bytes(name):
    return pkg_resources.resource_string(bytestagui.views.__name__, name)
