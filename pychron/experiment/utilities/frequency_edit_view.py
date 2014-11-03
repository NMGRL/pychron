# ===============================================================================
# Copyright 2014 Jake Ross
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
import os
import pickle
from traits.api import HasTraits, Bool, Str, Int, Property, List
from traitsui.api import View, Item, Controller
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.ui.combobox_editor import ComboboxEditor
from pychron.experiment.utilities.frequency_generator import validate_frequency_template
from pychron.paths import paths


class FrequencyModel(HasTraits):
    before = Bool(True)
    after = Bool(False)
    template = Property
    _template = Str

    frequency = Property
    _frequency = Int

    def _get_frequency(self):
        f = self.template
        if not f:
            f = self._frequency
        return f

    def _get_template(self):
        return self._template

    def _set_template(self, v):
        self._template = v

    def _validate_template(self, v):
        if not v.strip():
            return ''

        if validate_frequency_template(v):
            return v


TEMPLATE_HELP = '''use s to place run before group
use e to place run at the end of the group
use a list of numbers to place runs after the i-th run
use E to eliminate duplicate runs after one block and before the next block

Examples:
1. s          place before first run (B,-,-)
2. s,e        place before first run and after last (B,-,-,B)
3. s,2,4      place before first run, after third and fifth runs (B,-,-,B,-,-,B,-,-,-)
4. 3,5,e      place after third, fifth and last runs (-,-,B,-,-,B,-,-,-,B)
5. s,E        place before first run and after last exclusive (B,-,-,B,+,+,B)'''


class FrequencyEditView(Controller):
    templates = List(['s,e', 's,3,e'])

    def __init__(self, *args, **kw):
        super(FrequencyEditView, self).__init__(*args, **kw)
        self._load()

    def closed(self, info, is_ok):
        if is_ok:
            self._dump()

    def _dump(self):
        p = os.path.join(paths.hidden_dir, 'frequency_edit_view')
        with open(p, 'w') as fp:
            pickle.dump(self.templates, fp)

    def _load(self):
        p = os.path.join(paths.hidden_dir, 'frequency_edit_view')
        if os.path.isfile(p):
            with open(p, 'r') as fp:
                self.templates = pickle.load(fp)

    def traits_view(self):
        v = View(Item('_frequency'),
                 # Item('before'),
                 # Item('after'),
                 Item('template', tooltip=TEMPLATE_HELP,
                      editor=ComboboxEditor(name='controller.templates',
                                            addable=False)),
                 title='Edit Frequency Options',
                 buttons=['OK', 'Cancel'],
                 resizable=True)
        return v


if __name__ == '__main__':
    fm = FrequencyModel()
    fev = FrequencyEditView(model=fm)
    fev.configure_traits()
    print fm.frequency
# ============= EOF =============================================



