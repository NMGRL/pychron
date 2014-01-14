#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traitsui.api import View, VGroup, UItem, \
    HGroup, TableEditor, ButtonEditor
from traitsui.table_column import ObjectColumn
from traitsui.extras.checkbox_column import CheckboxColumn
from pyface.image_resource import ImageResource

from pychron.paths import paths

#============= standard library imports ========================
#============= local library imports  ==========================


class BatchEditPane(TraitsTaskPane):

    def _discrimination_group(self):
        cols = [
            ObjectColumn(name='name', editable=False),
            ObjectColumn(name='nominal_value',
                         width=75,
                         label='Value'),
            ObjectColumn(name='std_dev',
                         width=75,
                         label='Error'),
            CheckboxColumn(name='use', label='Use')]
        grp = VGroup(UItem('values', editor=TableEditor(columns=cols,
                                                        sortable=False, )),
                     label='Detectors')
        return grp

    def _blanks_group(self):
        cols = [
            ObjectColumn(name='name', editable=False),
            ObjectColumn(name='nominal_value',
                         width=75,
                         label='Value'),
            ObjectColumn(name='std_dev',
                         width=75,
                         label='Error'),
            CheckboxColumn(name='use', label='Use')]
        grp = VGroup(UItem('blanks', editor=TableEditor(columns=cols,
                                                        sortable=False)),
                     label='Blanks')
        return grp

    def _sensitivity_group(self):
        im = ImageResource(
            name='database_go.png',
            search_path=paths.icon_search_path)
        beditor = ButtonEditor(image=im)

        grp = VGroup(
            HGroup(
                UItem('sens_value', ),
                UItem('db_sens_button',
                      style='custom',
                      editor=beditor)),

            label='Sensitivity')

        return grp


    def traits_view(self):
        v = View(
            VGroup(
                self._discrimination_group(),
                self._blanks_group(),
                self._sensitivity_group()))
        return v

        #============= EOF =============================================
