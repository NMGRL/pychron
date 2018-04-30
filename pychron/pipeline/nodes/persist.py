# ===============================================================================
# Copyright 2015 Jake Ross
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
from __future__ import absolute_import
from __future__ import print_function

import csv
import os
from itertools import groupby

from pyface.message_dialog import information
from traits.api import Str, Instance, List, HasTraits, Bool, Float, Int, Button
from traitsui.api import Item, UItem, VGroup, HGroup, View
from traitsui.editors import DirectoryEditor, CheckListEditor, TableEditor
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn
from uncertainties import ufloat, std_dev, nominal_value

from pychron.core.confirmation import confirmation_dialog
from pychron.core.helpers.filetools import add_extension, unique_path2, view_file
from pychron.core.helpers.isotope_utils import sort_isotopes
from pychron.core.progress import progress_iterator
from pychron.core.ui.preference_binding import bind_preference
from pychron.core.ui.strings import SpacelessStr
from pychron.paths import paths
from pychron.pipeline.nodes.base import BaseNode
from pychron.pipeline.nodes.figure import FigureNode
from pychron.pipeline.nodes.persist_options import InterpretedAgePersistOptionsView, InterpretedAgePersistOptions
from pychron.pipeline.plot.editors.figure_editor import FigureEditor
from pychron.pipeline.plot.editors.interpreted_age_editor import InterpretedAgeEditor
from pychron.pipeline.state import get_isotope_set
from pychron.pipeline.tables.xlsx_table_options import XLSXTableWriterOptions
from pychron.pipeline.tables.xlsx_table_writer import XLSXTableWriter
from pychron.pipeline.tasks.interpreted_age_factory import set_interpreted_age
from six.moves import zip

from pychron.processing.analyses.analysis import EXTRACTION_ATTRS, META_ATTRS
from pychron.processing.analyses.analysis_group import InterpretedAgeGroup


class PersistNode(BaseNode):
    def configure(self, **kw):
        return True


class FileNode(PersistNode):
    root = Str
    extension = ''


class PDFNode(FileNode):
    extension = '.pdf'


class PDFFigureNode(PDFNode):
    name = 'PDF Figure'

    def configure(self, **kw):
        return BaseNode.configure(self, **kw)

    def traits_view(self):

        return self._view_factory(Item('root', editor=DirectoryEditor(root_path=paths.data_dir)),
                                  width=500)

    def _generate_path(self, ei):
        name = ei.name.replace(' ', '_')

        p, _ = unique_path2(self.root, name, extension=self.extension)
        return p

    def run(self, state):
        for ei in state.editors:
            if hasattr(ei, 'save_file'):
                print('save file to', self._generate_path(ei))
                ei.save_file(self._generate_path(ei))


class DVCPersistNode(PersistNode):
    dvc = Instance('pychron.dvc.dvc.DVC')
    commit_message = Str
    commit_tag = Str
    modifier = Str

    # def __init__(self, *args, **kwargs):
    #     super(DVCPersistNode, self).__init__(*args, **kwargs)

    def _persist(self, state, msg):
        mods = self.modifier
        if not isinstance(mods, tuple):
            mods = (self.modifier,)

        modp = []
        for mi in mods:
            modpi = self.dvc.update_analyses(state.unknowns,
                                             mi, '<{}> {}'.format(self.commit_tag, msg))
            modp.append(modpi)

        if modp:
            state.modified = True
            for m in modp:
                state.modified_projects = state.modified_projects.union(m)


class IsotopeEvolutionPersistNode(DVCPersistNode):
    name = 'Save Iso Evo'
    commit_tag = 'ISOEVO'
    modifier = ('intercepts', 'baselines')

    def run(self, state):
        if not state.saveable_keys:
            return

        wrapper = lambda x, prog, i, n: self._save_fit(x, prog, i, n, state.saveable_keys)
        progress_iterator(state.unknowns, wrapper, threshold=1)
        # for ai in state.unknowns:
        #     self.dvc.save_fits(ai, state.saveable_keys)

        msg = self.commit_message
        if not msg:
            f = ','.join('{}({})'.format(x, y) for x, y in zip(state.saveable_keys, state.saveable_fits))
            msg = 'fits={}'.format(f)

        self._persist(state, msg)

    def _save_fit(self, x, prog, i, n, keys):
        if prog:
            prog.change_message('Save Fits {} {}/{}'.format(x.record_id, i, n))

        self.dvc.save_fits(x, keys)


class BlanksPersistNode(DVCPersistNode):
    name = 'Save Blanks'
    commit_tag = 'BLANKS'
    modifier = 'blanks'

    def run(self, state):
        # if not state.user_review:
        # for ai in state.unknowns:
        #     self.dvc.save_blanks(ai, state.saveable_keys, state.references)
        wrapper = lambda x, prog, i, n: self._save_blanks(x, prog, i, n,
                                                          state.saveable_keys, state.references)
        progress_iterator(state.unknowns, wrapper, threshold=1)
        msg = self.commit_message
        if not msg:
            f = ','.join('{}({})'.format(x, y) for x, y in zip(state.saveable_keys, state.saveable_fits))
            msg = 'auto update blanks, fits={}'.format(f)

        self._persist(state, msg)

    def _save_blanks(self, ai, prog, i, n, saveable_keys, references):
        if prog:
            prog.change_message('Save Blanks {} {}/{}'.format(ai.record_id, i, n))
        # print 'sssss', saveable_keys
        self.dvc.save_blanks(ai, saveable_keys, references)


class ICFactorPersistNode(DVCPersistNode):
    name = 'Save ICFactor'
    commit_tag = 'ICFactor'
    modifier = 'icfactors'

    def run(self, state):
        wrapper = lambda ai, prog, i, n: self._save_icfactors(ai, prog, i, n,
                                                              state.saveable_keys,
                                                              state.saveable_fits,
                                                              state.references)
        progress_iterator(state.unknowns, wrapper, threshold=1)

        msg = self.commit_message
        if not msg:
            f = ','.join('{}({})'.format(x, y) for x, y in zip(state.saveable_keys, state.saveable_fits))
            msg = 'auto update ic_factors, fits={}'.format(f)

        self._persist(state, msg)

    def _save_icfactors(self, ai, prog, i, n, saveable_keys, saveable_fits, reference):
        if prog:
            prog.change_message('Save IC Factor for {} {}/{}'.format(ai.record_id, i, n))

        self.dvc.save_icfactors(ai, saveable_keys, saveable_fits, reference)


class FluxPersistNode(DVCPersistNode):
    name = 'Save Flux'
    commit_tag = 'FLUX'

    def run(self, state):
        if state.saveable_irradiation_positions:
            xs = [x for x in state.saveable_irradiation_positions if x.save]
            if xs:
                self.dvc.meta_repo.smart_pull()

                progress_iterator(xs,
                                  lambda *args: self._save_j(state, *args),
                                  threshold=1)

                p = self.dvc.meta_repo.get_level_path(state.irradiation, state.level)
                self.dvc.meta_repo.add(p)
                self.dvc.meta_commit('fit flux for {}'.format(state.irradiation, state.level))

                if confirmation_dialog('Would you like to share your changes?'):
                    self.dvc.meta_repo.smart_pull()
                    self.dvc.meta_repo.push()

    def _save_j(self, state, irp, prog, i, n):
        if prog:
            prog.change_message('Save J for {} {}/{}'.format(irp.identifier, i, n))

        decay = state.decay_constants
        self.dvc.save_j(irp.irradiation, irp.level, irp.hole_id, irp.identifier,
                        irp.j, irp.jerr,
                        irp.mean_j, irp.mean_jerr,
                        decay,
                        analyses=irp.analyses,
                        add=False)

        j = ufloat(irp.j, irp.jerr, tag='j')
        for i in state.unknowns:
            if i.identifier == irp.identifier:
                i.j = j
                i.arar_constants.lambda_k = decay['lambda_k_total']
                i.recalculate_age()


class XLSXTablePersistNode(BaseNode):
    name = 'Save Analysis Table'
    # auto_configure = False
    # configurable = False

    options_klass = XLSXTableWriterOptions

    def _finish_configure(self):
        self.options.dump()

    def run(self, state):
        bind_preference(self, 'skip_meaning', 'pychron.pipeline.skip_meaning')

        key = lambda x: x.group_id

        skip_meaning = self.skip_meaning
        options = self.options

        if options.table_kind == 'Step Heat':
            def factory(ans, tag='Human Table'):
                if skip_meaning:
                    if tag in skip_meaning:
                        ans = (ai for ai in ans if ai.tag.lower() != 'skip')

                return InterpretedAgeGroup(analyses=list(ans),
                                           plateau_nsteps=options.plateau_nsteps,
                                           plateau_gas_fraction=options.plateau_gas_fraction,
                                           fixed_step_low=options.fixed_step_low,
                                           fixed_step_high=options.fixed_step_high
                                           )

        else:
            def factory(ans, tag='Human Table'):
                if self.skip_meaning:
                    if tag in skip_meaning:
                        ans = (ai for ai in ans if ai.tag.lower() != 'skip')

                return InterpretedAgeGroup(analyses=list(ans))

        unknowns = list(a for a in state.unknowns if a.analysis_type == 'unknown')
        blanks = (a for a in state.unknowns if a.analysis_type == 'blank_unknown')
        airs = (a for a in state.unknowns if a.analysis_type == 'air')

        unk_group = [factory(analyses) for _, analyses in groupby(sorted(unknowns, key=key), key=key)]
        blank_group = [factory(analyses) for _, analyses in groupby(sorted(blanks, key=key), key=key)]
        air_group = [factory(analyses) for _, analyses in groupby(sorted(airs, key=key), key=key)]
        munk_group = [factory(analyses, 'Machine Table') for _, analyses in groupby(sorted(unknowns, key=key), key=key)]

        groups = {'unknowns': unk_group,
                  'blanks': blank_group,
                  'airs': air_group,
                  'machine_unknowns': munk_group}
        writer = XLSXTableWriter()

        for gs in groups.values():
            for gi in gs:
                gi.trait_set(plateau_nsteps=options.plateau_nsteps,
                             plateau_gas_fraction=options.plateau_gas_fraction,
                             fixed_step_low=options.fixed_step_low,
                             fixed_step_high=options.fixed_step_high)

        writer.build(groups, options=options)


class Isot(HasTraits):
    name = Str
    intercept_enabled = Bool(True)
    baseline_enabled = Bool(True)
    blank_enabled = Bool(True)
    bs_corrected_enabled = Bool(True)
    bl_corrected_enabled = Bool(True)
    ic_corrected_enabled = Bool(True)
    detector_enabled = Bool(True)

    def values(self):
        return (('{}_{}'.format(self.name, tag), getattr(self, '{}_enabled'.format(tag)))
                for tag in ('detector', 'intercept', 'blank', 'baseline', 'bs_corrected',
                            'bl_corrected', 'ic_corrected'))


class CSVAnalysesExportNode(BaseNode):
    name = 'Save CSV'
    pathname = SpacelessStr
    available_meta_attributes = List
    selected_meta_attributes = List

    available_isotopes = List
    available_ratios = List

    select_all_meta = Button('Select All')
    unselect_all_meta = Button('Unselect All')

    def traits_view(self):
        cols = [ObjectColumn(name='name', editable=False),
                CheckboxColumn(name='detector_enabled', label='Detector'),
                CheckboxColumn(name='intercept_enabled', label='Intercept'),
                CheckboxColumn(name='baseline_enabled', label='Baseline'),
                CheckboxColumn(name='blank_enabled', label='Blank'),
                CheckboxColumn(name='bs_corrected_enabled', label='Baseline Corrected'),
                CheckboxColumn(name='bl_corrected_enabled', label='Blank Corrected'),
                CheckboxColumn(name='ic_corrected_enabled', label='IC Corrected')]

        pgrp = HGroup(Item('pathname', springy=True, label='File Name'),
                      show_border=True)
        mgrp = VGroup(HGroup(UItem('select_all_meta'),
                             UItem('unselect_all_meta')),
                      UItem('selected_meta_attributes',
                            style='custom',
                            editor=CheckListEditor(cols=4,
                                                   name='available_meta_attributes'),
                            width=200),
                      show_border=True)
        igrp = VGroup(UItem('available_isotopes',
                            editor=TableEditor(columns=cols, sortable=False)),
                      show_border=True)

        return self._view_factory(VGroup(pgrp, mgrp, igrp))

    def run(self, state):
        p = os.path.join(paths.csv_data_dir, add_extension(self.pathname, '.csv'))

        with open(p, 'w') as wfile:
            writer = csv.writer(wfile)
            for ans in (state.unknowns, state.references):
                if ans:
                    header = self._get_header()
                    writer.writerow(header)
                    for ai in ans:
                        row = self._get_row(header, ai)
                        writer.writerow(row)

            if confirmation_dialog('File saved to {}\n\nWould you like to open?'.format(p)):
                view_file(p, application='Excel')

    def _configure_hook(self):
        if self.unknowns or self.references:
            uisokeys = get_isotope_set(self.unknowns)
            risokeys = get_isotope_set(self.references)
            isokeys = list(uisokeys.union(risokeys))
            self.available_isotopes = [Isot(name=i) for i in sort_isotopes(isokeys)]
            # if self.unknowns:
            #     ref = self.unknowns[0]
            # else:
            #     ref = self.references[0]
        temps = ('lab_temperature', 'east_diffuser_temperature', 'east_return_temperature', 'outside_temperature')
        self.available_meta_attributes = list(('rundate', 'timestamp') + META_ATTRS + EXTRACTION_ATTRS + temps)
        self._select_all_meta_fired()

    def _unselect_all_meta_fired(self):
        self.selected_meta_attributes = []

    def _select_all_meta_fired(self):
        self.selected_meta_attributes = self.available_meta_attributes

    def _get_header(self):
        header = self.selected_meta_attributes[:]

        vargs = [], [], [], [], [], [], []
        for i in self.available_isotopes:
            for vs, (name, enabled) in zip(vargs, i.values()):
                if enabled:
                    vs.append(name)
                    if not name.endswith('detector'):
                        vs.append('error')

        for va in vargs:
            header.extend(va)

        return header

    def _get_row(self, header, ai):

        def get_intercept(iso):
            return iso.uvalue

        def get_baseline_corrected(iso):
            return iso.get_baseline_corrected_value()

        def get_blank(iso):
            return iso.blank.uvalue

        def get_baseline(iso):
            return iso.baseline.uvalue

        def get_blank_corrected(iso):
            return iso.get_non_detector_corrected_value()

        def get_ic_corrected(iso):
            return iso.get_ic_corrected_value()

        row = []
        for attr in header:
            if attr == 'error':
                continue

            for tag, func in (('intercept', get_intercept),
                              ('blank', get_blank),
                              ('baseline', get_baseline),
                              ('bs_corrected', get_baseline_corrected),
                              ('bl_corrected', get_blank_corrected),
                              ('ic_corrected', get_ic_corrected)):
                if attr.endswith(tag):
                    # iso = attr[:len(tag) + 1]
                    args = attr.split('_')
                    iso = ai.get_isotope(args[0])
                    vs = ('', '')
                    if iso is not None:
                        v = func(iso)
                        vs = nominal_value(v), std_dev(v)

                    row.extend(vs)
                    break
            else:
                if attr.endswith('detector'):
                    args = attr.split('_')
                    iso = ai.get_isotope(args[0])
                    det = ''
                    if iso is not None:
                        det = iso.detector
                    row.append(det)
                else:
                    try:
                        # if attr.endswith('err'):
                        #     v = std_dev(ai.get_value(attr[-3:]))
                        # else:
                        v = nominal_value(ai.get_value(attr))
                    except BaseException:
                        v = ''

                    row.append(v)

        return row


# class TablePersistNode(FileNode):
#     pass
#
#
# class XLSTablePersistNode(BaseNode):
#     name = 'Save Analysis Table'
#     options_klass = AnalysisTablePersistOptionsView
#
#     def _options_factory(self):
#         opt = AnalysisTablePersistOptions(name='foo')
#         return self.options_klass(model=opt)
#
#     def run(self, state):
#         from pychron.pipeline.editors.arar_table_editor import ArArTableEditor
#
#         for editor in state.editors:
#             if isinstance(editor, ArArTableEditor):
#                 opt = self.options.model
#                 if opt.extension == 'xls':
#                     editor.make_xls_table(opt)
#                     view_file(opt.path)
#
#                     # basename = 'test_xls_table'
#                     # path, _ = unique_path2(paths.data_dir, basename, extension='.xls')
#                     # editor.make_xls_table('FooBar', path)
#
#

class SetInterpretedAgeNode(BaseNode):
    name = 'Set IA'
    dvc = Instance('pychron.dvc.dvc.DVC')

    def configure(self, pre_run=False, **kw):
        return True

    def run(self, state):
        for editor in state.editors:
            if isinstance(editor, InterpretedAgeEditor):
                ias = editor.get_interpreted_ages()
                set_interpreted_age(self.dvc, ias)


class InterpretedAgeTablePersistNode(BaseNode):
    name = 'Save IA Table'
    options_klass = InterpretedAgePersistOptionsView

    def _options_factory(self):
        opt = InterpretedAgePersistOptions(name='foo')
        return self.options_klass(model=opt)

    def run(self, state):
        from pychron.pipeline.editors.interpreted_age_table_editor import InterpretedAgeTableEditor
        for editor in state.editors:
            if isinstance(editor, InterpretedAgeTableEditor):
                opt = self.options.model
                if opt.extension == 'xlsx':
                    editor.make_xls_table(opt)
                    view_file(opt.path)

# ============= EOF =============================================
