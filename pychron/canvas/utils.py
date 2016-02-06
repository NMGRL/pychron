import struct


def load_holder_canvas(canvas, geom, **kw):
    if geom:
        if isinstance(geom, (str, unicode)):

            holes = [(x, y, r, str(c + 1))
                     for c, (x, y, r) in iter_geom(geom)]
        else:
            holes = geom

        canvas.load_scene(holes, **kw)


def iter_geom(geom, fmt='>fff', width=12):
    f = lambda x: struct.unpack(fmt, geom[x:x + width])
    return ((i, f(gi)) for i, gi in enumerate(xrange(0, len(geom), width)))


def make_geom(xyr, fmt='>fff'):
    return ''.join((struct.pack(fmt, *args)) for args in xyr)
