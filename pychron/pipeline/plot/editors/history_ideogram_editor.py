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
from traits.api import Range, HasTraits, List, Str, on_trait_change, Instance, Int
from traitsui.api import View, UItem, HGroup, VGroup, ListEditor, InstanceEditor

from pychron.pipeline.plot.editors.ideogram_editor import IdeogramEditor


class Opacity(HasTraits):
    value = Range(0, 100.0, 50)
    name = Str


class EditorOptions(HasTraits):
    opacities = List
    history_id = Int

    def traits_view(self):
        v = View(UItem('opacities', editor=ListEditor(style='custom',
                                                      editor=InstanceEditor(
                                                          view=View(HGroup(UItem('name', style='readonly'),
                                                                           UItem('value')))))))
        return v

    def set_items(self, ans):
        hids = sorted(list({a.history_id for a in ans}))
        self.opacities = [Opacity(name='H{}'.format(h), history_id=h) for h in hids]


class HistoryIdeogramEditor(IdeogramEditor):
    opacity = Range(0, 100.0, 50)
    editor_options = Instance(EditorOptions, ())

    def set_items(self, *args, **kw):
        super(HistoryIdeogramEditor, self).set_items(*args, **kw)
        self.editor_options.set_items(self.analyses)

    @on_trait_change('editor_options:opacities:value')
    def _handle_opacity(self, obj, name, old, new):
        new /= 100.
        # print(obj, name, old, new)
        for panel in self.figure_model.panels:
            figure = panel.figures[0]
            for i, plot in enumerate(figure.graph.plots):
                for vs in plot.plots.values():
                    for v in vs:
                        if v.history_id == obj.history_id:
                            self.set_opacity(v, new)

    def set_opacity(self, v, op):
        for attr in ('color', 'fill_color',
                     'selection_color', 'selection_outline_color',
                     'outline_color', 'edge_color'):
            try:
                cc = getattr(v, attr)
                if not isinstance(cc, tuple):
                    cc.setAlphaF(op)
                else:
                    cc = cc[:3] + (op,)
                setattr(v, attr, cc)
            except AttributeError:
                pass

    # def traits_view(self):
    #     v = View(VGroup(HGroup(UItem('opacity')),
    #                     self.get_component_view()),
    #              resizable=True)
    #     return v

# ============= EOF =============================================
