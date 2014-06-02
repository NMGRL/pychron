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
#===============================================================================

#============= enthought library imports =======================
from traits.api import Int, on_trait_change, Str, Property, cached_property
from traitsui.api import View, Item, EnumEditor
#============= standard library imports ========================
import ast
import yaml
#============= local library imports  ==========================
from pychron.core.helpers.ctx_managers import no_update
from pychron.core.helpers.filetools import list_directory2
from pychron.paths import paths
from pychron.pyscripts.context_editors.context_editor import ContextEditor


class MeasurementContextEditor(ContextEditor):
    #context values
    counts = Int(enter_set=True, auto_set=False)
    default_fits = Str(enter_set=True, auto_set=False)
    available_default_fits = Property


    #persistence
    def load(self, s):
        with no_update(self):
            s = self._extract_docstring(s)
            if s:
                ctx = yaml.load(s)
                for k, v in ctx.items():
                    setattr(self, k, v)

    def dump(self):
        ctx = {'default_fits': self.default_fits,
               'counts': self.counts, }

        return yaml.dump(ctx, default_flow_style=False)

    def generate_docstr(self):
        def gen():
            yield "'''"
            for di in reversed(self.dump().split('\n')):
                if di.strip():
                    yield di
            yield "'''"

        return list(gen())

    def _extract_docstring(self, s):
        m = ast.parse(s)
        return ast.get_docstring(m)

    @on_trait_change('counts, default_fits')
    def request_update(self):
        if self._no_update:
            return

        self.update_event = True

    @cached_property
    def _get_available_default_fits(self):
        return list_directory2(paths.fits_dir, extension='.yaml', remove_extension=True)

    def traits_view(self):
        v = View(Item('counts'),
                 Item('default_fits',
                      editor=EnumEditor(name='available_default_fits')))
        return v

#============= EOF =============================================
