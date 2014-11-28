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
from traits.api import Instance
from traitsui.api import Item, VGroup, Spring, HGroup, EnumEditor, UItem

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.experiment.automated_run.factory_view import FactoryView, POSITION_TOOLTIP


class UVFactoryView(FactoryView):
    model = Instance('pychron.experiment.automated_run.uv.factory.UVAutomatedRunFactory')

    def _get_group(self):
        sspring = lambda width=17: Spring(springy=False, width=width)
        extract_grp = VGroup(
            HGroup(sspring(width=33),
                   Item('extract_value', label='Extract',
                        tooltip='Set the extract value in extract units',
                        enabled_when='extractable'),
                   Item('extract_units',
                        show_label=False,
                        editor=EnumEditor(name='extract_units_names'))),

            HGroup(
                Item('cleanup', label='Cleanup (s)',
                     tooltip='Set the number of seconds to getter the sample gas')),
            HGroup(
                Item('mask', editor=EnumEditor(name='masks')),
                UItem('mask'),
                Item('attenuator'),
                Item('reprate')),
            HGroup(
                Item('position',
                     tooltip=POSITION_TOOLTIP)),
            label='Extract',
            show_border=True)

        return extract_grp

# ============= EOF =============================================
