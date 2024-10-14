from math import ceil

import cv2
from imageio import imread
from numpy import asarray
from skimage.exposure import rescale_intensity
from traits.has_traits import HasTraits
from traits.trait_types import Instance, Event, Button
from traitsui.item import UItem
from traitsui.view import View

from pychron.core.ui.image_editor import ImageEditor
from pychron.image.cv_wrapper import crop, get_size
from pychron.image.standalone_image import FrameImage


class Test(HasTraits):
    display_image = Instance(FrameImage, ())
    refresh_image = Event
    test = Button
    pxpermm = 38

    def _crop(self, frame, dim=1, pos=1):
        # if dim is None:
        #     hole = self._loading_manager.stage_manager.stage_map.get_hole(pos)
        #     dim = hole.dimension

        cw = ch = ceil(dim * 2.55)
        # pxpermm = self._loading_manager.stage_manager.autocenter_manager.pxpermm
        pxpermm = self.pxpermm
        cw_px = int(cw * pxpermm)
        ch_px = int(ch * pxpermm)
        w, h = get_size(frame)
        x = int((w - cw_px) / 2.0)
        y = int((h - ch_px) / 2.0)
        return asarray(crop(frame, x, y, cw_px, ch_px))

    def _get_image_from_path(self, p):
        img = imread(p)
        img = self._crop(img)
        return img

    def _test_fired(self):
        h = 3
        p = "~/mldata/mldata/421/filled/{}.filled.tif".format(h)
        filled_img = self._get_image_from_path(p)
        self.display_image.tile(filled_img)

        p = "~/mldata/mldata/421/empty/{}.map_pos.tif".format(h)
        empty_img = self._get_image_from_path(p)
        self.display_image.tile(empty_img)

        minus_img = cv2.subtract(filled_img, empty_img)
        self.display_image.tile(minus_img)

        rei = rescale_intensity(empty_img)
        rfi = rescale_intensity(filled_img)
        self.display_image.tile(rfi)
        self.display_image.tile(rei)

        minus_img = cv2.subtract(rfi, rei)
        self.display_image.tile(minus_img)

        self.display_image.tilify()

    def traits_view(self):
        v = View(
            UItem("test"),
            UItem(
                "object.display_image.source_frame",
                width=640,
                height=480,
                editor=ImageEditor(refresh="object.display_image.refresh_needed"),
            ),
            # width=900,
            # height=900,
        )
        return v


def main():
    t = Test()
    t.configure_traits()

    # blankframe = self._preprocess(blankframe)
    # blankframe = self._crop(blankframe, pos=pos)


if __name__ == "__main__":
    main()
