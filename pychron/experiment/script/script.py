#===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import Str, Any, Property, Button, cached_property, \
    String
from traitsui.api import View, HGroup, Label, spring, EnumEditor, UItem
#============= standard library imports ========================
import os
#============= local library imports  ==========================
from pychron.paths import paths
from pychron.pychron_constants import NULL_STR
from pychron.loggable import Loggable
import ast
import yaml


class Script(Loggable):
    application = Any
    label = Str
    mass_spectrometer = String

    name = Str
    names = Property(depends_on='mass_spectrometer')
    edit = Button
    kind = 'ExtractionLine'

    def get_parameter(self, key, default=None):
        p = os.path.join(self._get_root(), '{}_{}.py'.format(self.mass_spectrometer.lower(), self.name))
        if os.path.isfile(p):
            with open(p, 'r') as fp:
                text = fp.read()
                m = ast.parse(text)
                docstr = ast.get_docstring(m)
                if docstr is not None:
                    params = yaml.load(docstr)
                    try:
                        return params[key]
                    except KeyError:
                        pass
                    except TypeError:
                        self.warning('Invalid yaml docstring in {}. Could not retrieve {}'.format(self.name, key))

        return default

    def _edit_fired(self):
        p = os.path.join(paths.scripts_dir, self.label.lower(), '{}_{}.py'.format(self.mass_spectrometer,
                                                                                  self.name))
        app = self.application
        task = app.open_task('pychron.pyscript')

        task.kind = self.kind
        task.open(path=p)

    def traits_view(self):
        return View(HGroup(
            Label(self.label),
            spring,
            UItem('name',
                  width=-200,
                  editor=EnumEditor(name='names')),
            UItem('edit',
                  enabled_when='name and name!="---" and name is not "None"',
            ),
        )
        )

    def _clean_script_name(self, name):
        name = self._remove_mass_spectrometer_name(name)
        return self._remove_file_extension(name)

    def _remove_file_extension(self, name, ext='.py'):
        if name is NULL_STR:
            return NULL_STR

        if name.endswith('.py'):
            name = name[:-3]

        return name

    def _remove_mass_spectrometer_name(self, name):
        if self.mass_spectrometer:
            name = name.replace('{}_'.format(self.mass_spectrometer.lower()), '')
        return name

    def _get_root(self):
        d = self.label.lower().replace(' ', '_')
        p = os.path.join(paths.scripts_dir, d)
        return p

    def _load_script_names(self):
        p = self._get_root()
        if os.path.isdir(p):
            return [s for s in os.listdir(p)
                    if not s.startswith('.') and s.endswith('.py')]
        else:
            self.warning_dialog('{} script directory does not exist!'.format(p))

    @cached_property
    def _get_names(self):
        names = ['None']
        ms = self._load_script_names()
        if ms:
            msn = '{}_'.format(self.mass_spectrometer.lower())
            names.extend([self._clean_script_name(ei) for ei in ms if ei.startswith(msn)])

        return names

#============= EOF =============================================
