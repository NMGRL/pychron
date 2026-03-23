from pychron.core.helpers.color_utils import normalize_color_name

DEFAULT_CONTAINER_BGCOLOR = "white"
DEFAULT_PLOT_BGCOLOR = "white"
DEFAULT_CONTAINER_PADDING = 5


def themed_container_dict(**overrides):
    options = {
        "bgcolor": DEFAULT_CONTAINER_BGCOLOR,
        "padding": DEFAULT_CONTAINER_PADDING,
        "fill_padding": True,
    }
    options.update(overrides)
    if "bgcolor" in options:
        options["bgcolor"] = normalize_color_name(options["bgcolor"])
    return options


def themed_plot_bgcolor(color=None):
    return normalize_color_name(color or DEFAULT_PLOT_BGCOLOR)
