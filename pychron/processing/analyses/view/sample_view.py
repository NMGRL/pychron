# ===============================================================================
# Copyright 2022 ross
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
from traits.api import HasTraits, Str
from traitsui.api import View, UItem, VGroup

from pychron.core.pychron_traits import BorderHGroup


class SampleView(HasTraits):
    sample_prep_comment = Str
    sample_note = Str

    def __init__(self, an, *args, **kw):
        super(SampleView, self).__init__(*args, **kw)
        self.sample_prep_comment = an.sample_prep_comment
        self.sample_note = an.sample_note

    def traits_view(self):
        v = View(
            VGroup(
                BorderHGroup(UItem("sample_note"), label="Sample Note"),
                BorderHGroup(UItem("sample_prep_comment"), label="Sample Prep"),
            )
        )
        return v


# ============= EOF =============================================
