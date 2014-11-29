# ===============================================================================
# Copyright 2011 Jake Ross
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
from traits.api import HasTraits, String
from traitsui.api import View, Item

# ============= standard library imports ========================
import os
# ============= local library imports  ==========================
from pychron.modeling.model_data_directory import ModelDataDirectory

# ============= views ===================================
class SummaryView(HasTraits):
    summary = String
    activation_e = 10
    d_not = 10
    data = ''
    def selected_update(self, obj, name, old, new):
        if not isinstance(new, ModelDataDirectory):
            try:
                new = new[0]
            except (IndexError, TypeError):
                return
        try:
            if os.path.isdir(new.path):
                self._parse_diffusion_parameters(new.path)
        except AttributeError:
            pass

    def _parse_diffusion_parameters(self, root):

        ndomains = 0
        p = os.path.join(root, 'arr-me.in')
        if os.path.isfile(p):
            with open(p, 'r') as f:
                lines = [l for l in f]
                ndomains = int(lines[0].strip())
                self.activation_e = float(lines[1].strip())
                self.d_not = float(lines[-1].strip())

        # parse param.out
        p = os.path.join(root, 'param.out')
        if os.path.isfile(p):
            with open(p, 'r') as f:

                lines = [li.split('     ') for li in [l.strip() for l in f][-(2 + ndomains):-2]]
                ds = []
                for l in lines:
                    d = '\t'.join([li.strip() for li in l])
                    ds.append(d)
            self.data = '\n'.join(ds)

        self._build_summary()

    def _build_summary(self):

        header = '\t'.join(['Domain', 'Domain size', 'Volume fraction '])
        self.summary = '''
Ea = {:0.3f}
Do = {:0.3f}

{}
--------------------------
{}
        '''.format(self.activation_e,
             self.d_not,
             header,
             self.data
             )


    def traits_view(self):

        v = View(Item('summary', show_label=False,
                    style='custom',
                    ))
        return v
