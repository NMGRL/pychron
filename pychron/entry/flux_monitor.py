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
from traits.api import HasTraits, Float, Str, List
from traitsui.api import View, Item, HGroup, VGroup, EnumEditor
from pychron.pychron_constants import PLUSMINUS, SIGMA
#============= standard library imports ========================
#============= local library imports  ==========================

class FluxMonitor(HasTraits):
    name = Str
    dbname = Str
    names = List
    age = Float
    age_err = Float
    decay_constant = Float
    decay_constant_err = Float

    def _dbname_changed(self):
        self.name = self.dbname

    def traits_view(self):
        v = View(VGroup(
            HGroup(Item('name'), Item('dbname', show_label=False, editor=EnumEditor(name='names'))),
            HGroup(Item('age'), Item('age_err', label=u'{}1{}'.format(PLUSMINUS, SIGMA))),
            HGroup(Item('decay_constant'), Item('decay_constant_err', label=u'{}1{}'.format(PLUSMINUS, SIGMA)))
        ),
                 #                 HGroup(Item)
                 buttons=['OK', 'Cancel'],
                 title='Edit Flux Monitor'
        )
        return v

        #============= EOF =============================================
