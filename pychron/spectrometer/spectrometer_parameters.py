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
from traits.etsconfig.etsconfig import ETSConfig
ETSConfig.toolkit = 'qt4'

# ============= enthought library imports =======================
from traits.api import HasTraits, List, Instance, Str, Float, Any
from traitsui.api import View, UItem, TableEditor, ListEditor, Handler
from traitsui.table_column import ObjectColumn
# ============= standard library imports ========================
from ConfigParser import ConfigParser
import os
# ============= local library imports  ==========================
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.spectrometer import get_spectrometer_config_path


class Parameter(HasTraits):
    name = Str
    value = Float

class SpectrometerParameters(Loggable):
    groups = List

    spectrometer = Any

    def save(self):
        p = self.dump()
        msg = ''' Values saved to {}

Do you want to send these parameters to the spectrometer?
        
'''.format(p)
        if self.confirmation_dialog(msg):

            if self.spectrometer:
                self.spectrometer.send_configuration()

    def itervalues(self):
        for g in self.groups:
            for pa in g.parameters:
                yield g.name, pa.name, pa.value

    def load(self):
        cfp = ConfigParser()
        # p = os.path.join(paths.spectrometer_dir, 'config.cfg')
        p = get_spectrometer_config_path()
        cfp.read(p)
        gs = []
        for section in cfp.sections():
            g = SpectrometerParametersGroup(name=section)
            ps = []
            for pp in cfp.options(section):
                v = cfp.getfloat(section, pp)
                ps.append(Parameter(name=pp, value=v))

            g.parameters = ps
            gs.append(g)

        self.groups = gs

    def dump(self):
        p = get_spectrometer_config_path()

        cfp = ConfigParser()
        cfp.read(p)
        for gn, pn, v in self.itervalues():
            cfp.set(gn, pn, v)

        with open(p, 'w') as wfile:
            cfp.write(wfile)

        return p

class SpectrometerParametersGroup(HasTraits):
    parameters = List
    name = Str
    def traits_view(self):
        columns = [
                   ObjectColumn(name='name',
                                editable=False,
                              label='Name',
                              width=150
                              ),
                   ObjectColumn(name='value',
                              label='Value',
                              width=100
                              )
                  ]
        editor = TableEditor(columns=columns,
                             sortable=False
                             )
        v = View(UItem('parameters', style='custom',
                     editor=editor
                     ),
                 resizable=True,
                 width=300,
                 title='Spectrometer Settings'
               )

        return v

class SHandler(Handler):
    def closed(self, info, ok):
        if ok:
            info.object.save()


class SpectrometerParametersView(HasTraits):
    model = Instance('SpectrometerParameters')
    def trait_context(self):
        return {'object':self.model}

    def traits_view(self):
        v = View(UItem('groups',
                    style='custom',
                    editor=ListEditor(mutable=False,
                                      use_notebook=True,
                                      page_name='.name'
                                      )
                     ),
                 buttons=['OK', 'Cancel'],
                 handler=SHandler,
                 title='Spectrometer Settings',
                 kind='livemodal'
               )

        return v

if __name__ == '__main__':
    paths.build('_dev')
    s = SpectrometerParameters()
    s.load()
    v = SpectrometerParametersView(model=s)
    v.configure_traits()
# ============= EOF =============================================
