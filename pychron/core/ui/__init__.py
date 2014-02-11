def set_toolkit(name):
    from traits.etsconfig.etsconfig import ETSConfig

    ETSConfig.toolkit = name


def set_qt():
    set_toolkit('qt4')