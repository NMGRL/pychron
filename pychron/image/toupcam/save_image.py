# ===============================================================================
# Copyright 2015 Jake Ross
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

# ============= enthought library imports =======================
from numpy import load, random
import Image as pil
from numpy.core.umath import bitwise_or, bitwise_and
from traits.api import HasTraits, Str, Int, Bool, Any, Float, Property, on_trait_change
from traitsui.api import View, UItem, Item, HGroup, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
def main():
    im = load('/Users/ross/Desktop/image_uint32.npy')
    print im.shape, im.dtype
    pix = im[0,0]

    print pix, hex(pix)
    # im+=255
    # data = random.randint(0,2**16-1,(1000,1000))
    # im = pil.fromarray(data)
    # im.show()

    image = pil.fromarray(im, 'I')
    image.show()

if __name__ == '__main__':
    main()
# ============= EOF =============================================



