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
from traits.api import HasTraits, Bool, BaseStr, Directory, Int
from traitsui.api import View, HGroup, VGroup, Item
# ============= standard library imports ========================
import re
import os
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import add_extension
from pychron.entry.entry_views.entry import SpacelessStr

pascalcase_regex = re.compile(r'^[A-Z0-9]{1}\w*$')


class PascalCase(BaseStr):
    def validate(self, obj, name, value):
        if not value or not pascalcase_regex.match(value):
            self.error(obj, name, value)
        else:
            return value


class BaseSaveDialog(HasTraits):
    root = Directory

    @property
    def path(self):
        if self.root and self.name:
            return os.path.join(self.root, add_extension(self.name, '.txt'))


class IncrementalHeatTemplateSaveDialog(BaseSaveDialog):
    fname = SpacelessStr()
    n = Int

    def get_path(self):
        info = self.edit_traits()
        if info.result:
            return self.path

    @property
    def name(self):
        return '{:02n}-{}'.format(self.n, self.fname)

    def traits_view(self):
        ngrp = HGroup(Item('fname',
                           tooltip='No spaces in name. Name is automatically prefixed with the number of steps'))
        dgrp = HGroup(Item('root', label='Directory'))
        v = View(VGroup(ngrp, dgrp),
                 kind='livemodal',
                 width=400,
                 title='Save Step Heat Template',
                 buttons=['OK', 'Cancel'],
                 resizable=True)
        return v


class ExperimentSaveDialog(BaseSaveDialog):
    name = PascalCase()
    use_current_exp = Bool

    def _use_current_exp_changed(self, new):
        if new:
            self.name = 'CurrentExperiment'

    def traits_view(self):
        ngrp = HGroup(Item('name',
                           tooltip='Name must be in PascalCase. NoSpaces, use only AlphaNumeric'),
                      Item('use_current_exp'))
        dgrp = HGroup(Item('root', label='Directory'))
        v = View(VGroup(ngrp, dgrp),
                 kind='livemodal',
                 width=400,
                 title='Save Experiment',
                 buttons=['OK', 'Cancel'],
                 resizable=True)
        return v

# ============= EOF =============================================
