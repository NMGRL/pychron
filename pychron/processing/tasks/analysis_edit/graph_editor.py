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
from reportlab.lib.pagesizes import letter
from traits.api import Any, List, on_trait_change, Property, Event, File
from traits.trait_errors import TraitError
from traitsui.api import View, UItem, InstanceEditor
#============= standard library imports ========================
from numpy import asarray
import os
from itertools import groupby
import pickle
#============= local library imports  ==========================
from pychron.paths import paths
from pychron.processing.fits.fit_selector import FitSelector
from pychron.graph.regression_graph import StackedRegressionGraph
from pychron.processing.tasks.editor import BaseUnknownsEditor


class GraphEditor(BaseUnknownsEditor):
    tool = Any
    tool_klass = FitSelector
    graph = Any
    processor = Any

    analyses = List

    component = Property
    _component = Any

    component_changed = Event
    path = File
    basename = ''
    pickle_path = '_'
    unpack_peaktime = False
    calculate_age = True

    # auto_plot = Property
    # update_on_analyses = True
    recall_event = Event
    tag_event = Event
    invalid_event = Event

    def set_name(self):
        self._set_name()

    def set_auto_find(self, f):
        pass

    @on_trait_change('tool:save_event')
    def _handle_save_event(self):
        self.save_event = True

    @on_trait_change('analyses:[recall_event,tag_event, invalid_event]')
    def _handle_event(self, name, new):
        setattr(self, name, new)

    def make_title(self):
        names=[ai.record_id for ai in self.analyses]
        return self._grouped_name(names)

    def prepare_destroy(self):
        self.dump_tool()

    def dump_tool(self):
        if self.tool:
            p = os.path.join(paths.hidden_dir, self.pickle_path)
            self.debug('dumping tool {}, {}'.format(self.tool, p))
            with open(p, 'w') as fp:
                tool = self._get_dump_tool()
                pickle.dump(tool, fp)

    def _get_dump_tool(self):
        return dict(fits=self.tool.fits, auto_update=self.tool.auto_update)

    def load_tool(self, tool=None):
        p = os.path.join(paths.hidden_dir, self.pickle_path)
        if os.path.isfile(p):
            self.debug('loading tool at {}'.format(p))
            with open(p, 'r') as fp:
                try:
                    obj = pickle.load(fp)
                    if not obj:
                        os.unlink(p)
                    else:
                        self._load_tool(obj, tool=tool)

                except (pickle.PickleError, OSError, EOFError, AttributeError, ImportError, TraitError),e:
                    self.debug('exception loading tool {}'.format(e))
                    os.unlink(p)
                    return

    def _load_tool(self, tooldict, tool):
        if not isinstance(tooldict, dict):
            self.warning('invalid pickled tool {}'.format(type(tooldict)))
            return

        if tool is None:
            tool=self.tool

        tool.auto_update=tooldict['auto_update']

        fits=tooldict['fits']
        for fi in fits:
            ff = next((fo for fo in tool.fits if fo.name == fi.name), None)
            if ff:
                # self.debug('setting fit {} {} {}'.format(fi.name, fi.fit, fi.use))
                ff.trait_set(fit=fi.fit,
                             use=fi.use,
                             show=fi.show)

    def normalize(self, xs, start=None):
        xs = asarray(xs)
        xs.sort()
        if start is None:
            start = xs[0]
        xs -= start

        # scale to hours
        xs = xs / (60. * 60.)
        return xs

    def filter_invalid_analyses(self):
        # print items
        # if items is None:
        #     # f=lambda x: not x.tag=='invalid'
        #     self.analyses=[ai for ai in self.analyses
        #                    if ai.tag!='invalid']
        #     # self.analyses=filter(f, self.analyses)
        # else:
        #     for ai in self.analyses:
        #         if ai in items:
        #             self.analyses.remove(ai)
        self.analyses = [ai for ai in self.analyses if ai.tag != 'invalid']
        self.rebuild()

    def set_items(self, unks, is_append=False, **kw):
        ans = self.processor.make_analyses(unks,
                                            calculate_age=self.calculate_age,
                                            unpack=self.unpack_peaktime,
                                            **kw)

        if is_append:
            pans = self.analyses
            pans.extend(ans)
            ans = pans

        self.analyses=ans
        self._update_analyses()
        self.dump_tool()

    def _update_analyses(self):
        ans=self.analyses
        if ans:
            self.debug('analyses changed nanalyses={}'.format(len(ans)))
            self._compress_analyses(ans)

            refiso = ans[0]
            self._load_refiso(refiso)

            self._set_name()
            self._update_analyses_hook()
            # if self.auto_plot:
            self.rebuild_graph()
        else:
            self.debug('analyses changed {}'.format(ans))
            self._null_component()
            self.component_changed = True

    def _null_component(self):
        self.graph = self._graph_factory()

    def _load_refiso(self, refiso):
        self.load_fits(refiso)

    def load_fits(self, refiso):
        if refiso.isotope_keys:
            if self.tool:
                self.tool.load_fits(refiso.isotope_keys,
                                    refiso.isotope_fits)
            self.load_tool()

    def _set_name(self):
        na = list(set([ni.labnumber for ni in self.analyses]))
        na = self._grouped_name(na)
        self.name = '{} {}'.format(na, self.basename)

    def _update_analyses_hook(self):
        pass

    @on_trait_change('tool:update_needed')
    def _tool_refresh(self):
        self.debug('tool refresh')
        self.rebuild_graph()
        self.dump_tool()

    def rebuild(self, *args, **kw):
        pass

    def rebuild_graph(self):
        graph = self.graph

        graph.clear()
        self._rebuild_graph()

        self.component_changed = True

    def _rebuild_graph(self):
        pass

    def traits_view(self):
        v = View(UItem('graph',
                       style='custom',
                       editor=InstanceEditor(view='panel_view')))
        return v

    def _graph_default(self):
        return self._graph_factory()

    def _graph_factory(self, **kw):
        g = StackedRegressionGraph(container_dict=dict(stack_order='top_to_bottom',
                                                       use_backbuffer=True,
                                                       spacing=5), **kw)
        return g

    def _graph_generator(self):
        for fit in self.tool.fits:
            if fit.fit and fit.show:
                yield fit

    def _get_component(self):
        return self.graph.plotcontainer

    def save_file(self, path, force_layout=True, dest_box=None):
        _, tail = os.path.splitext(path)
        if tail not in ('.pdf', '.png'):
            path = '{}.pdf'.format(path)

        c = self.component

        '''
            chaco becomes less responsive after saving if 
            use_backbuffer is false and using pdf 
        '''
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

        self.rebuild_graph()

    def compress_analyses(self, ans=None):
        if ans is None:
            ans=self.analyses
        self._compress_analyses(ans)

    def _compress_analyses(self, ans):
        if not ans:
            return
        self._compress_graphs(ans)

    def _compress_graphs(self, ans):
        if not ans:
            return

        key = lambda x: x.graph_id
        ans = sorted(ans, key=key)
        groups = groupby(ans, key)
        try:
            mgid, analyses = groups.next()
        except StopIteration:
            return

        for ai in analyses:
            ai.graph_id = 0
        self._compress_groups(analyses)

        for gid, analyses in groups:
            for ai in analyses:
                ai.graph_id=gid-mgid

            self._compress_groups(analyses)

    def _compress_groups(self, ans):
        if not ans:
            return

        key = lambda x: x.group_id
        ans = sorted(ans, key=key)
        groups = groupby(ans, key)
        try:
            mgid, analyses = groups.next()
        except StopIteration:
            return

        for ai in analyses:
            ai.group_id = 0

        for gid, analyses in groups:
            for ai in analyses:
                ai.group_id = gid - mgid

    # def _get_auto_plot(self):
    #     return len(self.analyses) == 1 or self.update_on_analyses

    def _tool_default(self):
        t=self.tool_klass()
        self.load_tool(t)
        return t
#============= EOF =============================================
# def _gather_unknowns(self, refresh_data,
    #                      exclude='invalid',
    #                      compress_groups=True):
    #     '''
    #         use cached runs
    #
    #         use exclude keyward to specific tags that will not be
    #         gathered
    #
    #     '''
    #
    #     ans = self.unknowns
    #     if refresh_data or not ans:
    #         #ids = [ai.uuid for ai in self.analysis_cache]
    #         #aa = [ai for ai in self.unknowns if ai.uuid not in ids]
    #         #
    #         #nids = (ai.uuid for ai in self.unknowns if ai.uuid in ids)
    #         #bb = [next((ai for ai in self.analysis_cache if ai.uuid == i)) for i in nids]
    #         #aa = list(aa)
    #         #aa=self.unknowns
    #
    #         if ans:
    #             ans=self.processor.make_analyses(ans, exclude=exclude,
    #                                              calculate_age=self.calculate_age,
    #                                              unpack=self.unpack_peaktime)
    #
    #             #ans = timethis(self.processor.make_analyses,
    #             #               args=(ans,),
    #             #               kwargs={'exclude': exclude,
    #             #                       'calculate_age': self.calculate_age,
    #             #                       'unpack': self.unpack_peaktime},
    #             #               msg='MAKE ANALYSES TOTAL')
    #
    #
    #         if compress_groups:
    #             # compress groups
    #             self._compress_unknowns(ans)
    #
    #         #self.trait_set(unknowns=ans, trait_change_notify=False)
    #         self.unknowns = ans
    #     else:
    #         if exclude:
    #             ans = self.processor.filter_analysis_tag(ans, exclude)
    #
    #     return ans