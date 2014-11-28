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

#============= enthought library imports =======================
from traits.api import Instance
from traitsui.api import View, UItem, InstanceEditor

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.base_editor import BaseTraitsEditor
from pychron.graph.graph import Graph


class MassCalibrationEditor(BaseTraitsEditor):
    graph = Instance('pychron.graph.graph.Graph')

    name = 'Mass Cal'

    def traits_view(self):
        v = View(UItem('graph',
                       style='custom',
                       editor=InstanceEditor()))
        return v

    def _graph_default(self):
        return Graph(container_dict=dict(stack_order='top_to_bottom',
                                         padding=5,
                                         spacing=0
        ))


# ============= EOF =============================================

