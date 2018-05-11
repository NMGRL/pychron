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
from traits.api import Range
from traitsui.api import View, UItem, HGroup, VGroup

from pychron.pipeline.plot.editors.ideogram_editor import IdeogramEditor


class HistoryIdeogramEditor(IdeogramEditor):
    opacity = Range(0, 100.0, 50)

    def _opacity_changed(self, new):
        new /=100.
        for panel in self.figure_model.panels:
            figure = panel.figures[0]
            for i, plot in enumerate(figure.graph.plots):
                for vs in plot.plots.values():
                    for v in vs:
                        if v.group_id:
                            for attr in ('color', 'fill_color',
                                         'selection_color', 'selection_outline_color',
                                         'outline_color', 'edge_color'):
                                try:
                                    cc = getattr(v, attr)
                                    if not isinstance(cc, tuple):
                                        cc.setAlphaF(new)
                                    else:
                                        cc = cc[:3]+(new,)
                                    setattr(v, attr, cc)
                                except AttributeError:
                                    pass

        self.component.invalidate_and_redraw()

    def traits_view(self):
        v = View(VGroup(HGroup(UItem('opacity')),
                        self.get_component_view()),
                 resizable=True)
        return v

# ============= EOF =============================================
