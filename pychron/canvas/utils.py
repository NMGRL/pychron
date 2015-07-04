import struct


def load_holder_canvas(canvas, geom, **kw):
    if geom:
        if isinstance(geom, (str, unicode)):

            holes = [(x, y, r, str(c + 1))
                     for c, (x, y, r) in iter_geom(geom)]
        else:
            holes = geom

        canvas.load_scene(holes, **kw)


def iter_geom(geom):
    f = lambda x: struct.unpack('>fff', geom[x:x + 12])
    return ((i, f(gi)) for i, gi in enumerate(xrange(0, len(geom), 12)))