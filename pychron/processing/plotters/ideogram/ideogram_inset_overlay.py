# ===============================================================================
# Copyright 2014 Jake Ross
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

# ============= enthought library imports =======================

# ============= standard library imports ========================
# ============= local library imports  ==========================
from chaco.lineplot import LinePlot
from pychron.processing.plotters.base_inset import BaseInset

GOLDEN_RATIO = 1.618


class IdeogramInset(BaseInset, LinePlot):
    def __init__(self, *args, **kw):
        self.border_visible = kw.get('border_visible', True)
        BaseInset.__init__(self, *args, **kw)
        LinePlot.__init__(self)


# ============= EOF =============================================

