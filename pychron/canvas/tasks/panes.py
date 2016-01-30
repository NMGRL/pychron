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

# ============= enthought library imports =======================
from enable.component_editor import ComponentEditor
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traits.api import List
from traitsui.api import View, UItem, TreeEditor, TreeNode, HSplit

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.canvas.canvas2D.scene.layer import Layer
from pychron.canvas.canvas2D.scene.primitives.primitives import Primitive
from pychron.canvas.canvas2D.scene.scene import Scene


class PrimitiveNode(TreeNode):
    add = List([Primitive])
    move = List([Primitive])


class CanvasDesignerPane(TraitsTaskPane):
    def traits_view(self):
        nodes = [TreeNode(node_for=[Scene],
                          children='layers',
                          label='=layers',
                          auto_open=True
        ),
                 TreeNode(node_for=[Layer],
                          label='label',
                          children='components',
                          auto_open=True
                 ),
                 PrimitiveNode(node_for=[Primitive],
                               children='primitives',
                               label='label',
                 ),
        ]

        editor = TreeEditor(nodes=nodes,
                            selected='selected',
                            orientation='vertical')
        v = View(
            HSplit(
                UItem('scene',
                      editor=editor,
                      width=0.4
                ),
                UItem('canvas',
                      style='custom',
                      editor=ComponentEditor(),
                      width=0.6
                )
            )
        )

        return v


# ============= EOF =============================================
