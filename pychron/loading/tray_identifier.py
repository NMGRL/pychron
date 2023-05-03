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
from PIL import Image
from matplotlib import pyplot as plt
from numpy import asarray, arange, argmax, sin
from scipy.fft import fftfreq, rfftfreq, fft, rfft, irfft

from pychron.image.cv_wrapper import grayspace
from pychron.loggable import Loggable
from pychron.paths import paths


class TrayIdentifier(Loggable):
    def identify(self, frm):
        frm = self._preprocess_frame(frm)

        print(frm.shape)
        # get a single row of pixels
        # for i in range(-10, 10):
        #     row = frm[110+i, :]
        #     print(row)
        #
        #     plt.plot(arange(len(row)), row)
        #



        row = frm[110, :]

        # clip
        row = row[100:350]

        md = (row.max()-row.min())/2+row.min()
        nrow = ((row-md)/row.max())
        # t = max(row)*0.9
        # row[row > t] = 1
        # row[row <= t] = 0
        fig, axs = plt.subplots(3, 1)

        # c,r = frm.shape
        c = len(row)

        yf = rfft(nrow)
        xf = rfftfreq(c, 1)
        print(xf[argmax(abs(yf))])
        axs[0].plot(xf, abs(yf))
        axs[1].plot(arange(c), nrow)
        axs[2].plot(arange(c), row)
        # xs = arange(c)
        # f = xf[argmax(abs(yf))]
        # axs[2].plot(xs, sin(f*xs))
        # print(yf)

        n=len(yf)
        yf[-7*n//8:] = 0
        print(yf)
        axs[1].plot(irfft(yf))
        # plt.imshow(frm)
        plt.show()
        # identify peaks
        # calculate spacing between peaks

    def _preprocess_frame(self, frm):
        frm = grayspace(frm)
        return frm


if __name__ == '__main__':
    from pychron.core.helpers.logger_setup import logging_setup
    paths.build('Dev')
    logging_setup('tray_id', level='INFO')
    ti = TrayIdentifier()

    frm = Image.open('/Users/jross/Sandbox/snapshot-057.tif')

    ti.identify(asarray(frm))

# ============= EOF =============================================
