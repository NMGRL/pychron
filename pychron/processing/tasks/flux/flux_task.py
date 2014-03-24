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
from collections import namedtuple
import os
import struct

from traits.api import on_trait_change, List, HasTraits
from traitsui.tabular_adapter import TabularAdapter
from pyface.tasks.task_layout import TaskLayout, HSplitter, VSplitter, PaneItem, Tabbed









#============= standard library imports ========================
#============= local library imports  ==========================
from uncertainties import ufloat
from pychron.core.regression.mean_regressor import WeightedMeanRegressor
from pychron.database.records.isotope_record import IsotopeRecordView
from pychron.easy_parser import EasyParser
from pychron.paths import paths
from pychron.processing.analyses.analysis import Analysis
from pychron.processing.tasks.flux.flux_editor import FluxEditor
from pychron.processing.tasks.flux.flux_parser import XLSFluxParser, CSVFluxParser
from pychron.processing.tasks.flux.panes import IrradiationPane, AnalysesPane
from pychron.processing.tasks.analysis_edit.interpolation_task import InterpolationTask
from pychron.processing.tasks.analysis_edit.panes import TablePane
from pychron.processing.argon_calculations import calculate_flux

Position = namedtuple('Positon', 'position x y')


class LevelAdapter(TabularAdapter):
    columns = [('Run ID', 'identifier'), ('Pos.', ('position'))]
    #identifier_text = Property
    font = 'helvetica 10'

    #def _get_identifier_text(self):
    #print self.item
    #return self.item
    #return self.item.labnumber.identifier


class UnknownsAdapter(LevelAdapter):
    pass


class ReferencesAdapter(LevelAdapter):
    pass


class UnknownsPane(TablePane):
    id = 'pychron.processing.unknowns'
    name = 'Unknowns'


class ReferencesPane(TablePane):
    name = 'References'
    id = 'pychron.processing.references'


class GroupMarker(HasTraits):
    record_id = '------------'
    tag = '----'


class FluxTask(InterpolationTask):
    name = 'Flux'
    id = 'pychron.processing.flux'
    flux_editor_count = 1
    unknowns_adapter = UnknownsAdapter
    references_adapter = ReferencesAdapter
    references_pane_klass = ReferencesPane
    unknowns_pane_klass = UnknownsPane

    analyses = List

    def find_associated_analyses(self):
        pass

    def _default_layout_default(self):
        return TaskLayout(
            id='pychron.processing',
            left=HSplitter(
                VSplitter(
                    PaneItem('pychron.processing.irradiation'),
                    Tabbed(
                        PaneItem('pychron.processing.unknowns'),
                        PaneItem('pychron.processing.references'),
                        PaneItem('pychron.processing.analyses')),
                    PaneItem('pychron.processing.controls'))))

    def create_dock_panes(self):
        panes = super(FluxTask, self).create_dock_panes()
        return panes + [
            IrradiationPane(model=self.manager),
            AnalysesPane(model=self)]

    def new_flux(self):
        editor = FluxEditor(name='Flux {:03n}'.format(self.flux_editor_count),
                            processor=self.manager)

        self._open_editor(editor)
        self.flux_editor_count += 1

    @on_trait_change('manager:level')
    def _level_changed(self, new):
        if new:
            with self.manager.db.session_ctx():
                level = self.manager.get_level(new)
                if self.active_editor:
                    self.active_editor.level = level

                if level:
                    refs, unks = self.manager.group_level(level)
                    r, u = list(refs), list(unks)
                    self.unknowns_pane.items = u
                    self.references_pane.items = r

                    # self.active_editor.set_items(u)
                    # self.active_editor.references= r

    @on_trait_change('active_editor:tool:calculate_button')
    def _calculate_flux(self):
        if self.references_pane.items:
            editor = self.active_editor
            editor.monitor_positions = {}
            editor.positions_dirty = True
            editor.suppress_update = True
            db = self.manager.db
            with db.session_ctx():
                geom = self._get_geometry()
                editor.geometry = geom

                def add_pos(i, use=False):
                    if i.identifier:
                        ref = db.get_labnumber(i.identifier)
                        pid = ref.irradiation_position.position
                        ident = ref.identifier
                        sample = ''
                        if ref.sample:
                            sample = ref.sample.name

                        cj = ref.selected_flux_history.flux.j
                        cjerr = ref.selected_flux_history.flux.j_err
                        x, y, r = geom[pid - 1]

                        editor.add_position(int(pid), ident, sample, x, y, cj, cjerr, use)

                for ii in self.unknowns_pane.items:
                    add_pos(ii, use=False)

                for ii in self.references_pane.items:
                    add_pos(ii, use=True)

                editor.positions_dirty = True

                if editor.tool.data_source == 'database':
                    self._calculate_flux_db(editor)
                else:
                    self._calculate_flux_file(editor)

                editor.rebuild_graph()
                editor.set_predicted_j()
                editor.suppress_update = False

    def _calculate_flux_file(self, editor):
        #p = self.open_file_dialog()
        p = '/Users/ross/Sandbox/flux_visualizer/Tray I NM-261.xls'
        if p:
            #open flux file parser
            if p.endswith('.xls'):
                parser = XLSFluxParser(path=p)
            else:
                parser = CSVFluxParser(path=p)

            irrad, level = parser.get_irradiation()
            geom = self._get_geometry(irrad=irrad, level=level)
            editor.geometry = geom

            n = parser.get_npositions()
            prog = self.manager.open_progress(n=n)

            for pos in parser.iterpositions():

                pid = pos.hole_id

                prog.change_message('Loading Position {}'.format(pid))

                #get x,y from geometry
                try:
                    x, y, r = geom[pid - 1]
                    editor.add_monitor_position(pid, pos.identifier, x, y, pos.j, pos.je)
                except IndexError:
                    self.warning('Skipping hole {}. Only {} in this tray'.format(pid, len(geom)))
            prog.close()

    def _calculate_flux_db(self, editor):
        reg = WeightedMeanRegressor()
        reg.error_calc_type = editor.tool.mean_j_error_type
        monitor_age = editor.tool.monitor_age

        # helper funcs
        def mean_j(ans):
            ufs = (ai.uF for ai in ans)
            fs, es = zip(*((fi.nominal_value, fi.std_dev)
                           for fi in ufs))

            reg.trait_set(ys=fs, yserr=es)

            uf = (reg.predict([0]), reg.predict_error([0]))
            return ufloat(*calculate_flux(uf, monitor_age))

        proc = self.manager
        db = proc.db
        with db.session_ctx():
            refs = self.references_pane.items

            ans, tcs = zip(*[db.get_labnumber_analyses(ri.identifier, omit_key='omit_ideo')
                             for ri in refs])

            prog = proc.open_progress(n=sum(tcs), close_at_end=False)

            geom = self._get_geometry()
            editor = self.active_editor
            editor.geometry = geom

            for ais in ans:
                if ais:
                    ref = ais[0]
                    sj = ref.labnumber.selected_flux_history.flux.j
                    sjerr = ref.labnumber.selected_flux_history.flux.j_err

                    ident = ref.labnumber.identifier

                    aa = proc.make_analyses(ais, progress=prog)
                    n = len(aa)
                    j = mean_j(aa)
                    dev = 100
                    if sj:
                        dev = (j.nominal_value - sj) / sj * 100

                    if editor.tool.save_mean_j:
                        db.save_flux(ident, j.nominal_value, j.std_dev, inform=False)
                        sj, sjerr = j.nominal_value, j.std_dev

                    d = dict(saved_j=sj, saved_jerr=sjerr,
                             mean_j=j.nominal_value, mean_jerr=j.std_dev,
                             dev=dev, n=n)

                    editor.set_position_j(ident, **d)

            prog.close()

    def _get_geometry(self, irrad=None, level=None, holder=None):
        man = self.manager

        db = man.db
        with db.session_ctx():
            if holder is None:
                if irrad is None:
                    irrad = man.irradiation
                    level = man.level

                level = db.get_irradiation_level(irrad, level)
                holder = level.holder
            else:
                holder = db.get_irradiation_holder(holder)

            geom = holder.geometry
            return [struct.unpack('>fff', geom[i:i + 12])
                    for i in xrange(0, len(geom), 12)]

    @on_trait_change('unknowns_pane:[items, update_needed, dclicked, refresh_editor_needed]')
    def _update_unknowns_runs(self, obj, name, old, new):
        if name == 'dclicked':
            if new:
                if isinstance(new.item, (IsotopeRecordView, Analysis)):
                    self._recall_item(new.item)
        elif name == 'refresh_editor_needed':
            self.active_editor.rebuild()
            # else:
            #     if not obj._no_update:
            #         if self.active_editor:
            #             self.active_editor.set_items(self.unknowns_pane.items)
            #         if self.plot_editor_pane:
            #             self.plot_editor_pane.analyses = self.unknowns_pane.items

    def _active_editor_changed(self):
        if self.active_editor:
            if self.controls_pane:
                tool = None
                if hasattr(self.active_editor, 'tool'):
                    tool = self.active_editor.tool

                self.controls_pane.tool = tool

                # if self.unknowns_pane:
                #     # if hasattr(self.unknowns_pane, 'previous_selections'):
                #     #     self.unknowns_pane.previous_selection = self.unknowns_pane.previous_selections[0]
                #     if hasattr(self.active_editor, 'analyses'):
                #         #if self.active_editor.unknowns:
                #         self.unknowns_pane.items = self.active_editor.analyses


    def do_easy_flux(self):
        path = os.path.join(paths.dissertation, 'data', 'minnabluff', 'flux.yaml')
        ep = EasyParser(path=path)
        # db = self.manager.db
        doc = ep.doc('flux')

        # projects = doc['projects']
        # identifiers = doc.get('identifiers')
        levels = doc.get('levels')
        # editor = FluxEditor(processor=self)
        # prog=self.manager.open_progress(n=len(levels))

        if levels:
            editor = self.active_editor
            mon_age = doc.get('monitor_age', 28.201e6)
            editor.tool.monitor_ge = mon_age
            for li_str in levels:
                irrad, level = li_str.split(' ')
                # print irrad, level
                self.manager.irradiation = irrad
                self.manager.level = level
                # print self.manager

                #         #unknowns and refs now loaded
                self._calculate_flux()
                #         self._calculate_flux_db(self.active_editor)
                #
                #         #update flux in db for all positions
                # editor.set_save_all(True)
                editor.set_save_unknowns(True)
                editor.save()
        # prog.close()
        return True

#============= EOF =============================================
