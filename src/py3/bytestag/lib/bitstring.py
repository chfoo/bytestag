try:
    from bitstring import *  # @UnusedWildImport

    # FIXME: I don't know why nosetests messes this up
    try:
        Bits
    except NameError:
        from bytestag.lib._bitstring import *  # @UnusedWildImport

except ImportError:
    from ._bitstring import *  # @UnusedWildImport

assert Bits
