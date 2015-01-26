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
from traits.api import HasTraits, Str, Int, Bool, Any, Float, Property, on_trait_change, List
from traitsui.api import View, UItem, Item, HGroup, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.editors import ListEditor
from pychron.globals import globalv
from pychron.paths import paths
from pychron.processing.plotters.options.base import BasePlotterOptions
from pychron.processing.plotters.options.isochron import InverseIsochronOptions
from pychron.processing.plotters.options.spectrum import SpectrumOptions


class CompositeOptions(BasePlotterOptions):
    suboptions = List
    # def __init__(self, proot, *args, **kw):
    #     super(CompositeOptions, self).__init__(*args, **kw)
    def _dump(self, root):
        pass

    def get_options(self, kind):
        return next((o for o in self.suboptions
                     if kind in o.__class__.__name__.lower()), None)

    def traits_view(self):
        v=View(UItem('suboptions',
                     style='custom',
                     editor=ListEditor(use_notebook=True)))
        return v

    def _suboptions_default(self):
        sp=os.path.join(paths.plotter_options_dir,
                        globalv.username,'spectrum')

        ip=os.path.join(paths.plotter_options_dir,
                        globalv.username,'inverse_isochron')

        s =[SpectrumOptions(sp),
            InverseIsochronOptions(ip)]
        return s
# ============= EOF =============================================



