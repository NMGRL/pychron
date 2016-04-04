from kiva.agg import GraphicsContextArray


def save(gc, filename, file_format=None, pil_options=None):
    """ Save the GraphicsContext to a file.  Output files are always
        saved in RGB or RGBA format; if this GC is not in one of
        these formats, it is automatically converted.

        If filename includes an extension, the image format is
        inferred from it.  file_format is only required if the
        format can't be inferred from the filename (e.g. if you
        wanted to save a PNG file as a .dat or .bin).

        filename may also be "file-like" object such as a
        StringIO, in which case a file_format must be supplied

        pil_options is a dict of format-specific options that
        are passed down to the PIL image file writer.  If a writer
        doesn't recognize an option, it is silently ignored.

        If the image has an alpha channel and the specified output
        file format does not support alpha, the image is saved in
        rgb24 format.
    """
    FmtsWithoutAlpha = ('jpg', 'bmp', 'eps', "jpeg")
    from PIL import Image as PilImage
    size = (gc.width(), gc.height())
    fmt = gc.format()

    # determine the output pixel format and PIL format
    if fmt.endswith("32"):
        pilformat = "RGBA"
        pixelformat = "rgba32"
        if (isinstance(filename, basestring) and filename[-3:].lower() in FmtsWithoutAlpha) or \
           (file_format is not None and file_format.lower() in FmtsWithoutAlpha):
            pilformat = "RGB"
            pixelformat = "rgb24"
    elif fmt.endswith("24"):
        pilformat = "RGB"
        pixelformat = "rgb24"

    # perform a conversion if necessary
    if fmt != pixelformat:
        newimg = GraphicsContextArray(size, fmt)
        newimg.draw_image(gc)
        newimg.convert_pixel_format(pixelformat, 1)
        bmp = newimg.bmp_array
    else:
        bmp = gc.bmp_array

    img = PilImage.frombytes(pilformat, size, bmp.tostring())
    img.save(filename, format=file_format, options=pil_options)