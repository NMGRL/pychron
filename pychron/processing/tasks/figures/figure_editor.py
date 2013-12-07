#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from chaco.base_plot_container import BasePlotContainer
from traits.api import Any, on_trait_change, \
    List
from traitsui.api import View, UItem
from enable.component_editor import ComponentEditor as EnableComponentEditor
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.processing.tasks.analysis_edit.graph_editor import GraphEditor
from pychron.processing.tasks.figures.annotation import AnnotationTool, AnnotationOverlay


class FigureEditor(GraphEditor):
    table_editor = Any
    component = Any
    plotter_options_manager = Any
    associated_editors = List

    tool = Any

    annotation_tool = Any

    figure_model = Any

    def _null_component(self):
        self.component = BasePlotContainer()

    @on_trait_change('figure_model:panels:figures:refresh_unknowns_table')
    def _handle_refresh(self, obj, name, old, new):
        self.refresh_unknowns_table = True
        #if not obj.suppress_associated:
        #print 'figure editor refresh', id(self)
        for e in self.associated_editors:
            if isinstance(e, FigureEditor):
                #e.rebuild_graph()
                if e.model:
                    for p in e.model.panels:
                        for f in p.figures:
                            f.replot()

    def traits_view(self):
        v = View(UItem('component',
                       style='custom',
                       width=650,
                       editor=EnableComponentEditor()))
        return v

    def add_text_box(self):
        if self.annotation_tool is None:
            an = AnnotationOverlay(component=self.component)
            at = AnnotationTool(an, components=[an])
            an.tools.append(at)
            self.annotation_tool = at
            self.component.overlays.append(an)

        elif not self.annotation_tool.active:
            an = AnnotationOverlay(component=self.component)
            self.annotation_tool.components.append(an)
            self.annotation_tool.component = an
            an.tools.append(self.annotation_tool)
            self.component.overlays.append(an)

        else:
            self.annotation_tool = None

    def set_group(self, idxs, gid, refresh=True):

        for i, uu in enumerate(self.unknowns):
            if i in idxs:
                uu.group_id = gid

        if refresh:
            self.rebuild(refresh_data=False)

    def _rebuild_graph(self):
        self.rebuild(refresh_data=False)

    def _update_unknowns_hook(self):
        ans = self.unknowns
        for e in self.associated_editors:
            if isinstance(e, FigureEditor):
                e.unknowns = ans
            else:
                e.items = ans

    def rebuild(self, refresh_data=False, compress_groups=True):
        ans = self._gather_unknowns(refresh_data, compress_groups=compress_groups)

        if ans:
            po = self.plotter_options_manager.plotter_options
            #model, comp = timethis(self.get_component, args=(ans, po),
            #                       msg='get_component {}'.format(self.__class__.__name__))
            model, comp = self.get_component(ans, po)
            if comp:
                comp.invalidate_and_redraw()
                self.figure_model = model
                self.component = comp
                self.component_changed = True

    def get_component(self, ans, po):
        pass






#============= EOF =============================================
#
#     def _gather_unknowns_cached(self):
#         if self._cached_unknowns:
#             # removed items:
# #             if len(self.unknowns) < len(self._cached_unknowns):
#             # added items
# #             else:
#
#             # get analyses not loaded
#             cached_recids = [ui.record_id for ui in self._cached_unknowns]
#             nonloaded = [ui for ui in self.unknowns
#                             if not ui.record_id in cached_recids]
#             if nonloaded:
#                 nonloaded = self.processor.make_analyses(nonloaded)
#                 self.processor.load_analyses(nonloaded)
#                 self._unknowns.extend(nonloaded)
#
#             # remove analyses in _unknowns but not in unknowns
#             recids = [ui.record_id for ui in self.unknowns]
#             ans = [ui for ui in  self._unknowns
#                    if ui.record_id in recids]
# #             for i,ci in enumerate(self._cached_unknowns):
# #                 if ci in self.unknowns:
# #             ans = self._unknowns
# #             ans = [ui for ui, ci in zip(self._unknowns, self._cached_unknowns)
# #                                     if ci in self.unknowns]
#         else:
#             unks = self.unknowns
#             unks = self.processor.make_analyses(unks)
#             self.processor.load_analyses(unks)
#             ans = unks
#
# #         self._cached_unknowns = self.unknowns[:]
#         if ans:
#
#             # compress groups
#             self._compress_unknowns(ans)
#
#             self._unknowns = ans
#             return ans
