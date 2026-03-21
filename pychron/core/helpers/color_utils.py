from __future__ import annotations

from collections.abc import Sequence

from pychron.core.helpers.color_generators import colors8i


COLOR_NAME_ALIASES = {
    "light grey": "lightgray",
    "dark grey": "darkgray",
    "grey": "gray",
    "light grey": "lightgray",
    "darkgrey": "darkgray",
    "lightgrey": "lightgray",
    "blue violet": "blueviolet",
    "lime green": "limegreen",
    "green yellow": "greenyellow",
    "transparent": "clear",
}


def normalize_color_name(color):
    if not isinstance(color, str):
        return color

    value = color.strip().lower()
    if not value:
        return value

    if value.startswith("#"):
        return value

    return COLOR_NAME_ALIASES.get(value, value.replace(" ", ""))


def _call_or_value(value):
    return value() if callable(value) else value


def _extract_rgba_components(color):
    if color is None:
        return None

    if isinstance(color, str):
        normalized = normalize_color_name(color)
        if normalized in ("clear", "none"):
            return 0, 0, 0, 0
        if normalized in colors8i:
            r, g, b = colors8i[normalized]
            return r, g, b, 255
        return None

    if isinstance(color, Sequence) and not isinstance(color, (bytes, bytearray)):
        comps = list(color)
    elif hasattr(color, "rgba"):
        rgba = _call_or_value(getattr(color, "rgba"))
        if isinstance(rgba, int):
            return (
                (rgba >> 16) & 255,
                (rgba >> 8) & 255,
                rgba & 255,
                (rgba >> 24) & 255,
            )
        comps = list(rgba)
    elif all(hasattr(color, attr) for attr in ("red", "green", "blue")):
        comps = [
            _call_or_value(getattr(color, "red")),
            _call_or_value(getattr(color, "green")),
            _call_or_value(getattr(color, "blue")),
        ]
        alpha = getattr(color, "alpha", None)
        if alpha is not None:
            comps.append(_call_or_value(alpha))
    else:
        return None

    if not comps:
        return None

    if len(comps) == 3:
        comps.append(1.0 if max(comps) <= 1 else 255)
    elif len(comps) < 3:
        return None

    if max(comps) <= 1:
        comps = [int(round(component * 255)) for component in comps]
    else:
        converted = []
        for index, component in enumerate(comps[:4]):
            if index == 3 and isinstance(component, float) and component <= 1:
                converted.append(int(round(component * 255)))
            else:
                converted.append(int(round(component)))
        comps = converted

    return tuple(max(0, min(255, int(component))) for component in comps[:4])


def to_rgba255(color, default=None):
    comps = _extract_rgba_components(color)
    if comps is None:
        if default is None:
            return None
        comps = _extract_rgba_components(default)
    return comps


def to_rgba_float(color, default=None):
    comps = to_rgba255(color, default=default)
    if comps is None:
        return None
    return tuple(component / 255.0 for component in comps)


def to_hex(color, include_alpha=False, default=None):
    comps = to_rgba255(color, default=default)
    if comps is None:
        return None
    if include_alpha:
        return "#{:02x}{:02x}{:02x}{:02x}".format(*comps)
    return "#{:02x}{:02x}{:02x}".format(*comps[:3])


def contrast_color(color, dark="black", light="white"):
    comps = to_rgba255(color)
    if comps is None:
        return dark

    r, g, b, _ = comps
    luminance = (0.299 * r) + (0.587 * g) + (0.114 * b)
    return dark if luminance >= 186 else light


def coerce_qcolor(color, qcolor_class=None, default=None):
    if qcolor_class is None:
        try:
            from pyface.qt import QtGui
        except Exception:
            return None

        qcolor_class = QtGui.QColor

    if isinstance(color, qcolor_class):
        return color

    comps = to_rgba255(color, default=default)
    if comps is not None:
        return qcolor_class(*comps)

    normalized = normalize_color_name(color)
    try:
        return qcolor_class(normalized)
    except Exception:
        return None
