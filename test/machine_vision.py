# ===============================================================================
# Copyright 2013 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

#============= enthought library imports =======================

import unittest

from pychron.mv.focus.autofocus_manager import AutoFocusManager
from pychron.image.video import Video
from pychron.globals import globalv

#============= standard library imports ========================
#============= local library imports  ==========================

class FocusTest(unittest.TestCase):
    def setUp(self):
        globalv.video_test = True
        globalv.video_test_path = '/Users/ross/Sandbox/pos_err/pos_err_221_0-005.jpg'
        v = Video()

        self.auto_focus = AutoFocusManager(video=v)

    def testFocusMeasure(self):
        af = self.auto_focus

        src = af._load_source()
        operator = 'laplace'
        roi = 0, 0, 100, 100
        a = af._calculate_focus_measure(src, operator, roi)
        self.assertEqual(a, 782)

# ============= EOF =============================================
