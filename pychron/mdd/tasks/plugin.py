# ===============================================================================
# Copyright 2018 ross
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
from traits.api import List

from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.mdd.tasks.nodes import AgesMeNode, ArrMeNode, FilesNode, MDDWorkspaceNode, MDDFigureNode, \
    AutoAgeFreeNode, MDDLabTableNode, AutoAgeMonNode, AutoArrNode, CorrFFTNode, ConfIntNode, ArrMultiNode
from pychron.mdd.tasks.predefined import LABTABLE, FILES, ARRME, AGESME, AUTOARR, AUTOAGEMON, MDDFIGURE, AUTOAGEFREE, \
    CORRFFT, CONFINT, ARRMULTI
from pychron.mdd.tasks.preferences import MDDPreferencesPane
from pychron.paths import paths


class MDDPlugin(BaseTaskPlugin):
    nodes = List(contributes_to='pychron.pipeline.nodes')
    predefined_templates = List(contributes_to='pychron.pipeline.predefined_templates')

    def _preferences_panes_default(self):
        return [MDDPreferencesPane]

    def _executable_path_changed(self, new):
        if new:
            paths.clovera_root = new

    def _predefined_templates_default(self):
        return [('MDD', (('LabTable', LABTABLE),
                         ('Files', FILES),
                         ('ArrMulti', ARRMULTI),
                         ('AutoArr', AUTOARR),
                         ('ArrMe', ARRME),
                         ('AgesMe', AGESME),
                         ('CorrFFT', CORRFFT),
                         ('ConfInt', CONFINT),
                         ('AutoAgeMon', AUTOAGEMON),
                         ('AutoAgeFree', AUTOAGEFREE),
                         ('MDD Figure', MDDFIGURE)))]

    def _nodes_default(self):
        return [AutoArrNode, AgesMeNode, ArrMeNode, FilesNode,
                MDDWorkspaceNode, MDDFigureNode, MDDLabTableNode,
                AutoAgeFreeNode,
                AutoAgeMonNode, CorrFFTNode, ConfIntNode, ArrMultiNode]

# ============= EOF =============================================
