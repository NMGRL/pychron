from __future__ import absolute_import

import struct


def load_holder_canvas(canvas, geom, **kw):
    if geom:
        if isinstance(geom, str):
            holes = [(x, y, r, str(c + 1)) for c, (x, y, r) in iter_geom(geom)]
        else:
            holes = geom

        canvas.load_scene(holes, **kw)


def iter_geom(geom, fmt=">fff", width=12):
    def f(x):
        return struct.unpack(fmt, geom[x : x + width])

    return ((i, f(gi)) for i, gi in enumerate(range(0, len(geom), width)))


def make_geom(xyr, fmt=">fff"):
    return b"".join((struct.pack(fmt, *args)) for args in xyr).decode("utf-8")


def markup_canvas_position(canvas, dbpos, monitor_name):
    cgen = (
        "#{:02x}{:02x}{:02x}".format(*ci)
        for ci in ((194, 194, 194), (255, 255, 160), (255, 255, 0), (25, 230, 25))
    )

    def set_color(ii, value):
        if ii is not None:
            if value:
                ii.fill_color = next(cgen)

    if dbpos:
        v = ""
        if dbpos.identifier:
            v = str(dbpos.identifier)

        item = canvas.scene.get_item(str(dbpos.position))
        item.fill = True
        if v:
            set_color(item, v)

        dbsam = dbpos.sample
        if dbsam:
            sample_name = dbsam.name
            item.measured_indicator = dbpos.analyzed

            if sample_name == monitor_name:
                item.monitor_indicator = True

            set_color(item, sample_name)
            if dbsam.material:
                set_color(item, dbsam.material.name)

            if dbsam.project:
                set_color(item, dbsam.project.name)


def markup_canvas(canvas, positions, monitor_name):
    for p in positions:
        markup_canvas_position(canvas, p, monitor_name)


# ============= EOF =============================================
