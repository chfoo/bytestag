try:
    from pkg_resources import *  # @UnusedWildImport

    # FIXME: I don't know why nosetests messes this up
    try:
        resource_string  # @UndefinedVariable
    except NameError:
        from bytestag.lib._pkg_resources import *  # @UnusedWildImport

except ImportError:
    from ._pkg_resources import *  # @UnusedWildImport
