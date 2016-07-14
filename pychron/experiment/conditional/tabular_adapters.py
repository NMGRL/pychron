# ===============================================================================
# Copyright 2016 Jake Ross
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
from traits.api import Str, Int, Property
from traitsui.tabular_adapter import TabularAdapter

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.resources import icon
from pychron.experiment.utilities.conditionals import level_text, level_color


GREENBALL = icon('green_ball')


class BaseConditionalsAdapter(TabularAdapter):
    level_text = Property
    tripped_text = Str('')
    tripped_image = Property

    def get_bg_color(self, obj, trait, row, column=0):
        item = getattr(obj, trait)[row]
        return level_color(item.level)

    def _get_level_text(self):
        return level_text(self.item.level)

    def _get_tripped_image(self):
        if self.item.tripped:
            return GREENBALL


class PRConditionalsAdapter(BaseConditionalsAdapter):
    columns = [('Tripped', 'tripped'),
               ('Level', 'level'),
               ('Attribute', 'attr'),
               ('Check', 'teststr'),
               ('Location', 'location')]

    attr_width = Int(100)
    teststr_width = Int(200)


class ConditionalsAdapter(BaseConditionalsAdapter):
    columns = [('Tripped', 'tripped'),
               ('Level', 'level'),
               ('Attribute', 'attr'),
               ('Start', 'start_count'),
               ('Frequency', 'frequency'),
               ('Check', 'teststr'),
               ('Location', 'location')]

    attr_width = Int(75)
    teststr_width = Int(175)
    start_width = Int(50)
    frequency_width = Int(75)


class EPRConditionalsAdapter(PRConditionalsAdapter):
    columns = [('Attribute', 'attr'),
               ('Check', 'teststr')]


class EConditionalsAdapter(ConditionalsAdapter):
    columns = [('Attribute', 'attr'),
               ('Start', 'start_count'),
               ('Frequency', 'frequency'),
               ('Check', 'teststr')]


class EActionConditionalsAdapter(ConditionalsAdapter):
    columns = [('Attribute', 'attr'),
               ('Start', 'start_count'),
               ('Frequency', 'frequency'),
               ('Check', 'teststr'),
               ('Action', 'action')]


class EModificationConditionalsAdapter(ConditionalsAdapter):
    columns = [('Attribute', 'attr'),
               ('Start', 'start_count'),
               ('Frequency', 'frequency'),
               ('Check', 'teststr'),
               ('Action', 'action'),
               ('Skip N', 'nskip'),
               ('Truncate', 'use_truncation'),
               ('Terminate', 'use_termination')]

    use_termination_text = Property
    use_truncation_text = Property
    action_width = Int(150)

    def _get_use_termination_text(self):
        return 'Yes' if self.item.use_termination else 'No'

    def _get_use_truncation_text(self):
        return 'Yes' if self.item.use_truncation else 'No'
# ============= EOF =============================================
