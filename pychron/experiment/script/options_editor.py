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
from pychron.core.ui import set_qt

set_qt()

# ============= enthought library imports =======================
from traits.api import HasTraits, Str, Any, List
from traitsui.api import View, UItem, HGroup

from traitsui.editors import TableEditor
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn
# ============= standard library imports ========================
import os
import yaml
# ============= local library imports  ==========================


class Option(HasTraits):
    name = Str
    value = Any


class OptionsEditor(HasTraits):
    path = Str
    numeric_options = List
    bool_options = List

    def _path_changed(self):
        if self.path and os.path.isfile(self.path):
            with open(self.path, 'r') as fp:
                try:
                    d = yaml.load(fp)
                except yaml.YAMLError:
                    return

                opts = []
                bopts = []
                for k, v in d.iteritems():
                    opt = Option(name=k, value=v)
                    if isinstance(v, bool):
                        bopts.append(opt)
                    else:
                        opts.append(opt)
                self.numeric_options = opts
                self.bool_options = bopts

    def traits_view(self):
        ncols = [ObjectColumn(name='name', editable=False),
                 ObjectColumn(name='value')]

        bcols = [ObjectColumn(name='name', editable=False),
                 CheckboxColumn(name='value')]

        v = View(HGroup(UItem('numeric_options',
                              editor=TableEditor(columns=ncols), ),
                        UItem('bool_options',
                              editor=TableEditor(columns=bcols))),
                 resizable=True,
                 title='Script Options',
                 buttons=['OK', 'Cancel'])
        return v


if __name__ == '__main__':
    v = OptionsEditor()
    v.path = '/Users/ross/Programming/git/pychron_dev/test/data/script_options.yaml'
    v.configure_traits()

# ============= EOF =============================================

