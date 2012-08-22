import bytestag.ui.views
import pkg_resources


def get_bytes(name):
    return pkg_resources.resource_string(bytestag.ui.views.__name__, name)
