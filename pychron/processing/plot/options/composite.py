# ===============================================================================
# Copyright 2015 Jake Ross
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

from traits.api import on_trait_change, List
from traitsui.api import View, UItem


# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.editors import ListEditor
from pychron.globals import globalv
from pychron.paths import paths
from pychron.processing.plot.options.base import BasePlotterOptions
from pychron.processing.plot.options.isochron import InverseIsochronOptions
from pychron.processing.plot.options.spectrum import SpectrumOptions


class CompositeOptions(BasePlotterOptions):
    suboptions = List
    # def __init__(self, proot, *args, **kw):
    #     super(CompositeOptions, self).__init__(*args, **kw)

    def _load_factory_defaults(self, yd):
        so1 = self.suboptions[0]
        so2 = self.suboptions[1]

        so1.trait_set(**yd[0]['padding'])
        so2.trait_set(**yd[1]['padding'])

    def _load(self, root):
        p = os.path.join(root, '{}.options'.format(self.name))
        if os.path.isfile(p):
            with open(p, 'r') as rfile:
                suboptions = pickle.load(rfile)
                for si in suboptions:
                    si.load(os.path.join(root, si.name))
                self.suboptions = suboptions

    def _dump(self, root):
        droot = os.path.join(root, self.name)
        for option in self.suboptions:
            option.dump(droot)

        with open(os.path.join(root, '{}.options'.format(self.name)), 'w') as wfile:
            pickle.dump(self.suboptions, wfile)


    def get_options(self, kind):
        return next((o for o in self.suboptions
                     if kind in o.__class__.__name__.lower()), None)

    def traits_view(self):
        v=View(UItem('suboptions',
                     style='custom',
                     editor=ListEditor(use_notebook=True,
                                       page_name='.label')))
        return v

    @on_trait_change('suboptions:refresh_plot_needed')
    def _handle_refresh(self):
        self.refresh_plot_needed = True

    def _suboptions_default(self):
        sp=os.path.join(paths.plotter_options_dir,
                        globalv.username,'spectrum')

        ip=os.path.join(paths.plotter_options_dir,
                        globalv.username,'inverse_isochron')

        s =[SpectrumOptions(sp),
            InverseIsochronOptions(ip)]
        return s
# ============= EOF =============================================



