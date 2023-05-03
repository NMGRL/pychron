# ===============================================================================
# Copyright 2023 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================
import json
import os

from PIL import Image
from matplotlib import pyplot as plt
from numpy import asarray, arange, argmax, sin, histogram, diff, gradient
import scipy.signal as signal
from scipy.fft import fftfreq, rfftfreq, fft, rfft, irfft

from pychron.image.cv_wrapper import grayspace
from pychron.loggable import Loggable
from pychron.paths import paths


class TrayCodeReader(Loggable):
    def identify(self, frm):
        frm = self._preprocess_frame(frm)
        # fig, axs = plt.subplots(2, 1)

        allpeaks = []
        clip_max, clip_min = 400, 100
        for i in range(10):
            row = frm[100 + i, :]

            # clip row
            row = row[clip_min:clip_max]

            nrow = self._preprocess_scanline(row)

            peaks = signal.find_peaks(nrow, prominence=0.30)[0]

            allpeaks.extend(peaks)
            # break

        barwidth = 10
        nbins = (clip_max - clip_min) // barwidth

        mp = min(allpeaks)
        counts, edges = histogram(allpeaks, bins=nbins)
        centers = (edges[:-1] + edges[1:]) // 2
        lines = centers[counts > 0]
        bits = []
        bitspacing = 29   # 29 pixels between bits

        for bi in range(9):
            bitt = mp + (bi * bitspacing)
            for li in lines:
                if abs(li - bitt) < barwidth:
                    bits.append(1)
                    break
            else:
                bits.append(0)

            # axs[1].axvline(bitt, color='green')

        # axs[0].hist(allpeaks, bins=nbins)
        # axs[0].set_xlim(0, len(row))
        # axs[1].set_xlim(0, len(row))
        # plt.show()

        # bits = int(''.join(map(str, bits)),2)
        bitstr = ''.join(map(str, bits))
        return bitstr

    def get_tray_name_by_id(self, tid):
        self.debug(f'get tray name for id={tid}')
        tc = os.path.join(paths.map_dir, 'tray_codes.json')
        with open(tc, 'r') as rfile:
            tray_codes = json.load(rfile)
            return tray_codes.get(str(tid))

    def _preprocess_scanline(self, row):
        md = (row.max() - row.min()) / 2 + row.min()
        nrow = ((row - md) / row.max())
        return nrow

    def _preprocess_frame(self, frm):
        frm = grayspace(frm)
        return frm


if __name__ == '__main__':
    from pychron.core.helpers.logger_setup import logging_setup

    paths.build('~/PychronDirs/PychronDev')
    logging_setup('tray_id', level='INFO')
    ti = TrayCodeReader()

    frm = Image.open('/Users/jross/Sandbox/snapshot-0572.tif')

    tid = ti.identify(asarray(frm))
    print('tray ided as {}'.format(tid))
    print(ti.get_tray_name_by_id(tid))

# ============= EOF =============================================
