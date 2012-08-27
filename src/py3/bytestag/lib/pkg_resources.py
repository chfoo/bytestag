try:
    from pkg_resources import *

    # FIXME: I don't know why nosetests messes this up
    try:
        resource_string  # @UndefinedVariable
    except NameError:
        from bytestag.lib._pkg_resoureces import *

except ImportError:
    from ._pkg_resoureces import *
