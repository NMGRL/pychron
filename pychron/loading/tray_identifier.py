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
from numpy import asarray, arange, argmax
from numpy.fft import fftfreq
from scipy.fft import fft

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

        # t = max(row)*0.9
        # row[row > t] = 1
        # row[row <= t] = 0
        fig, axs = plt.subplots(2, 1)

        c,r = frm.shape
        yf = fft(row)
        xf = fftfreq(c, 1)[:c//2]
        print(xf[argmax(abs(yf))])
        axs[0].plot(xf, 2.0/c * abs(yf[0:c//2]))
        axs[1].plot(arange(len(row)), row)



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
    logging_setup('tray_id')
    ti = TrayIdentifier()

    frm = Image.open('/Users/jross/Sandbox/snapshot-057.tif')

    ti.identify(asarray(frm))

# ============= EOF =============================================
