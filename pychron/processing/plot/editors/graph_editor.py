# ===============================================================================
# Copyright 2013 Jake Ross
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

from traits.api import List, Property, Event, cached_property
from traitsui.api import View, UItem
from enable.component_editor import ComponentEditor as EnableComponentEditor


# ============= standard library imports ========================
from itertools import groupby
# ============= local library imports  ==========================
from pychron.processing.tasks.editor import BaseUnknownsEditor


class GraphEditor(BaseUnknownsEditor):
    analyses = List
    refresh_needed = Event
    component = Property(depends_on='refresh_needed')
    basename = ''

    def save_file(self, path, force_layout=True, dest_box=None):
        _, tail = os.path.splitext(path)
        if tail not in ('.pdf', '.png'):
            path = '{}.pdf'.format(path)

        c = self.component

        '''
            chaco becomes less responsive after saving if
            use_backbuffer is false and using pdf
        '''
        from reportlab.lib.pagesizes import letter

        c.do_layout(size=letter, force=force_layout)

        _, tail = os.path.splitext(path)
        if tail == '.pdf':
            from chaco.pdf_graphics_context import PdfPlotGraphicsContext

            gc = PdfPlotGraphicsContext(filename=path,
                                        dest_box=dest_box)
            gc.render_component(c, valign='center')
            gc.save()

        else:
            from chaco.plot_graphics_context import PlotGraphicsContext

            gc = PlotGraphicsContext((int(c.outer_width), int(c.outer_height)))
            gc.render_component(c)
            gc.save(path)

            # self.rebuild_graph()

    def set_items(self, ans, is_append=False):
        if is_append:
            self.analyses.extend(ans)
        else:
            self.analyses = ans

        if self.analyses:
            self._set_name()
            self._compress_groups()
            self.refresh_needed = True

    def _set_name(self):
        na = list(set([ni.labnumber for ni in self.analyses]))
        na = self._grouped_name(na)
        self.name = '{} {}'.format(na, self.basename)

    def _compress_groups(self):
        ans = self.analyses
        if not ans:
            return

        key = lambda x: x.group_id
        ans = sorted(ans, key=key)
        groups = groupby(ans, key)
        # try:
        # mgid, analyses = groups.next()
        # except StopIteration:
        #     return

        # print 'compress groups'
        # for ai in analyses:
        # ai.group_id = 0

        for i, (gid, analyses) in enumerate(groups):
            for ai in analyses:
                # ai.group_id = gid - mgid
                ai.group_id = i

    @cached_property
    def _get_component(self):
        ans = self.analyses
        if ans:
            return self._component_factory()

            # po = self.plotter_options_manager.plotter_options
            # model, comp = timethis(self.get_component, args=(ans, po),
            # msg='get_component {}'.format(self.__class__.__name__))
            # model, comp = self.get_component(ans, po)
            # if comp:
            # comp.invalidate_and_redraw()
            #     self.figure_model = model
            #     return comp
                # self.component = comp
                # self.component_changed = True

    def _component_factory(self):
        raise NotImplementedError

    def traits_view(self):
        v = View(UItem('component',
                       style='custom',
                       width=650,
                       editor=EnableComponentEditor()),
                 resizable=True)
        return v

# class GraphEditor(BaseUnknownsEditor):
# tool = Any
#     tool_klass = FitSelector
#     graph = Any
#     processor = Any
#
#     analyses = List
#
#     component = Property
#     _component = Any
#
#     component_changed = Event
#     path = File
#     basename = ''
#     pickle_path = '_'
#     unpack_peaktime = False
#     calculate_age = True
#
#     # auto_plot = Property
#     # update_on_analyses = True
#     recall_event = Event
#     tag_event = Event
#     invalid_event = Event
#     update_graph_on_set_items = False
#
#     def set_name(self):
#         self._set_name()
#
#     def set_auto_find(self, f):
#         pass
#
#     def make_title(self):
#         names = [ai.record_id for ai in self.analyses]
#         return self._grouped_name(names)
#
#     def prepare_destroy(self):
#         self.dump_tool()
#
#     def dump_tool(self):
#         tool = self._get_dump_tool()
#         if tool:
#             p = os.path.join(paths.hidden_dir, self.pickle_path)
#             self.debug('dumping tool {}, {}'.format(tool, p))
#             with open(p, 'w') as wfile:
#                 pickle.dump(tool, wfile)
#
#     def load_tool(self, tool=None):
#         p = os.path.join(paths.hidden_dir, self.pickle_path)
#         if os.path.isfile(p):
#             self.debug('loading tool at {}'.format(p))
#             with open(p, 'r') as rfile:
#                 try:
#                     obj = pickle.load(rfile)
#                     if not obj:
#                         os.unlink(p)
#                     else:
#                         self._load_tool(obj, tool=tool)
#
#                 except (pickle.PickleError, OSError, EOFError, AttributeError, ImportError, TraitError), e:
#                     self.debug('exception loading tool {}'.format(e))
#                     os.unlink(p)
#                     return
#
#     def normalize(self, xs, start=None):
#         xs = asarray(xs)
#         xs.sort()
#         if start is None:
#             start = xs[0]
#         xs -= start
#
#         # scale to hours
#         xs /= 60. * 60.
#         return xs
#
#     # def filter_invalid_analyses(self):
#     # self.analyses = [ai for ai in self.analyses if ai.tag != 'invalid']
#     # self.rebuild()
#
#     def set_items(self, unks, is_append=False, update_graph=None, **kw):
#
#         if any((isinstance(ai, FileAnalysis) for ai in unks)):
#             ans = unks
#         else:
#
#             ans = self.processor.make_analyses(unks, calculate_age=self.calculate_age,
#                                                unpack=self.unpack_peaktime,
#                                                **kw)
#         if is_append:
#             pans = self.analyses
#             pans.extend(ans)
#             ans = pans
#
#         if update_graph is None:
#             update_graph = self.update_graph_on_set_items
#
#         self.analyses = ans
#         # self.trait_setq(analyses=ans)
#         self._update_analyses(update_graph=update_graph)
#
#     def load_fits(self, refiso):
#         if refiso.isotope_keys:
#             if self.tool:
#                 refs = refiso.isotope_keys[:]
#                 self.tool.load_fits(refs,
#                                     refiso.get_isotope_fits())
#             self.load_tool()
#
#     def rebuild(self, *args, **kw):
#         pass
#
#     @caller
#     def rebuild_graph(self):
#         graph = self.graph
#
#         graph.clear()
#         self._rebuild_graph()
#
#         self.component_changed = True
#
#     def save_file(self, path, force_layout=True, dest_box=None):
#         _, tail = os.path.splitext(path)
#         if tail not in ('.pdf', '.png'):
#             path = '{}.pdf'.format(path)
#
#         c = self.component
#
#         '''
#             chaco becomes less responsive after saving if
#             use_backbuffer is false and using pdf
#         '''
#         from reportlab.lib.pagesizes import letter
#
#         c.do_layout(size=letter, force=force_layout)
#
#         _, tail = os.path.splitext(path)
#         if tail == '.pdf':
#             from chaco.pdf_graphics_context import PdfPlotGraphicsContext
#
#             gc = PdfPlotGraphicsContext(filename=path,
#                                         dest_box=dest_box)
#             gc.render_component(c, valign='center')
#             gc.save()
#
#         else:
#             from chaco.plot_graphics_context import PlotGraphicsContext
#
#             gc = PlotGraphicsContext((int(c.outer_width), int(c.outer_height)))
#             gc.render_component(c)
#             gc.save(path)
#
#         self.rebuild_graph()
#
#     def compress_analyses(self, ans=None):
#         if ans is None:
#             ans = self.analyses
#         self._compress_analyses(ans)
#
#     def traits_view(self):
#         v = View(UItem('graph',
#                        style='custom',
#                        editor=InstanceEditor(view='panel_view')))
#         return v
#
#     # private
#     def _get_dump_tool(self):
#         if self.tool:
#             return dict(fits=self.tool.fits, auto_update=self.tool.auto_update)
#
#     def _load_tool(self, tooldict, tool):
#         if not isinstance(tooldict, dict):
#             self.warning('invalid pickled tool {}'.format(type(tooldict)))
#             return
#
#         if tool is None:
#             tool = self.tool
#
#         tool.auto_update = tooldict['auto_update']
#
#         fits = tooldict['fits']
#         for fi in fits:
#             ff = next((fo for fo in tool.fits if fo.name == fi.name), None)
#             if ff:
#                 # self.debug('setting fit {} {} {}'.format(fi.name, fi.fit, fi.use))
#                 ff.trait_set(fit=fi.fit,
#                              use=fi.use,
#                              show=fi.show)
#
#     def _set_name(self):
#         na = list(set([ni.labnumber for ni in self.analyses]))
#         na = self._grouped_name(na)
#         self.name = '{} {}'.format(na, self.basename)
#
#     def _update_analyses_hook(self):
#         pass
#
#     def _rebuild_graph(self):
#         pass
#
#     def _graph_generator(self):
#         for fit in self.tool.fits:
#             if fit.fit and fit.show:
#                 yield fit
#
#     def _get_component(self):
#         return self.graph.plotcontainer
#
#     def _compress_analyses(self, ans):
#         if not ans:
#             return
#         self._compress_graphs(ans)
#
#     def _compress_graphs(self, ans):
#         if not ans:
#             return
#
#         key = lambda x: x.graph_id
#         ans = sorted(ans, key=key)
#         groups = groupby(ans, key)
#         try:
#             mgid, analyses = groups.next()
#         except StopIteration:
#             return
#
#         for ai in analyses:
#             ai.graph_id = 0
#         self._compress_groups(analyses)
#
#         for gid, analyses in groups:
#             for ai in analyses:
#                 ai.graph_id = gid - mgid
#
#             self._compress_groups(analyses)
#
#     def _compress_groups(self, ans):
#         if not ans:
#             return
#
#         key = lambda x: x.group_id
#         ans = sorted(ans, key=key)
#         groups = groupby(ans, key)
#         try:
#             mgid, analyses = groups.next()
#         except StopIteration:
#             return
#
#         for ai in analyses:
#             ai.group_id = 0
#
#         for gid, analyses in groups:
#             for ai in analyses:
#                 ai.group_id = gid - mgid
#
#     def _update_analyses(self, update_graph=False):
#         ans = self.analyses
#         if ans:
#             self.debug('analyses changed nanalyses={}'.format(len(ans)))
#             self._compress_analyses(ans)
#
#             refiso = ans[0]
#             self._load_refiso(refiso)
#
#             self._set_name()
#             self._update_analyses_hook()
#             if update_graph:
#                 # if self.auto_plot:
#                 self.rebuild_graph()
#         else:
#             self.debug('analyses changed {}'.format(ans))
#             self._null_component()
#             self.component_changed = True
#
#     def _null_component(self):
#         self.graph = self._graph_factory()
#
#     def _load_refiso(self, refiso):
#         self.load_fits(refiso)
#
#     # handlers
#     @on_trait_change('tool:save_event')
#     def _handle_save_event(self):
#         self.save_event = True
#
#     @on_trait_change('analyses:[recall_event,tag_event, invalid_event]')
#     def _handle_event(self, name, new):
#         setattr(self, name, new)
#
#     @on_trait_change('tool:update_needed')
#     def _tool_refresh(self):
#         self.debug('tool refresh')
#         self.rebuild_graph()
#         self.dump_tool()
#
#     def _graph_factory(self, **kw):
#         from pychron.graph.stacked_regression_graph import StackedRegressionGraph
#
#         g = StackedRegressionGraph(container_dict=dict(stack_order='top_to_bottom',
#                                                        use_backbuffer=True,
#                                                        spacing=5), **kw)
#         return g
#
#     def _tool_default(self):
#         t = self.tool_klass()
#         self.load_tool(t)
#         return t
#
#     def _graph_default(self):
#         return self._graph_factory()


# ============= EOF =============================================
