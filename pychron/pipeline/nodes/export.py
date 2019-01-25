# ===============================================================================
# Copyright 2019 ross
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

import csv
import os

from traits.api import HasTraits, Str, Bool, List, Button, Enum
from traitsui.api import VGroup, HGroup, UItem, Item, CheckListEditor, TableEditor
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn
from uncertainties import nominal_value, std_dev

from pychron.core.confirmation import confirmation_dialog
from pychron.core.helpers.filetools import add_extension, view_file
from pychron.core.helpers.isotope_utils import sort_isotopes
from pychron.core.pychron_traits import BorderHGroup
from pychron.core.ui.strings import SpacelessStr
from pychron.paths import paths
from pychron.pipeline.nodes.base import BaseNode
from pychron.pipeline.state import get_isotope_set
from pychron.processing.analyses.analysis import META_ATTRS, EXTRACTION_ATTRS


class CSVExportNode(BaseNode):
    delimiter = Enum(',', '\t', ':', ';')
    available_isotopes = List
    pathname = SpacelessStr

    def run(self, state):
        p = os.path.join(paths.csv_data_dir, add_extension(self.pathname, '.csv'))

        with open(p, 'w') as wfile:
            writer = csv.writer(wfile, delimiter=self.delimiter)
            for ans in (state.unknowns, state.references):
                if ans:
                    self._run_hook(writer, ans)

            if confirmation_dialog('File saved to {}\n\nWould you like to open?'.format(p)):
                view_file(p, application='Excel')

    def _run_hook(self, writer, ans):
        raise NotImplementedError

    def _set_available_isotopes(self):
        if self.unknowns or self.references:
            uisokeys = get_isotope_set(self.unknowns)
            risokeys = get_isotope_set(self.references)
            isokeys = list(uisokeys.union(risokeys))
            self.available_isotopes = [self._isotope_klass(name=i) for i in sort_isotopes(isokeys)]


class RawIsot(HasTraits):
    name = Str
    time = Bool(True)
    intensity = Bool(True)

    @property
    def header(self):
        h = []
        if self.time:
            h.append('{}Time'.format(self.name).upper())
        if self.intensity:
            h.append('{}Intensity'.format(self.name).upper())
        return h


class CSVRawDataExportNode(CSVExportNode):
    name = 'Save CSV Raw Data'
    _isotope_klass = RawIsot

    def traits_view(self):
        pgrp = BorderHGroup(Item('pathname', springy=True, label='File Name'),
                            Item('delimiter'))

        cols = [ObjectColumn(name='name'),
                CheckboxColumn(name='time'),
                CheckboxColumn(name='intensity')]

        igrp = VGroup(UItem('available_isotopes', editor=TableEditor(columns=cols, sortable=False)))
        return self._view_factory(VGroup(pgrp, igrp))

    def _configure_hook(self):
        self._set_available_isotopes()

    def _run_hook(self, writer, analyses):
        def writedata(d):
            for i, row in enumerate(d):
                row = [str(ri) for ri in row]
                writer.writerow([i + 1, ] + row)
            writer.writerow([])

        for a in analyses:
            a.load_raw_data()
            writer.writerow(['RUNID', 'UUID', 'PROJECT', 'SAMPLE', 'REPOSITORY'])
            writer.writerow([a.record_id, a.uuid, a.project, a.sample, a.repository_identifier])
            header = self._get_header(a)
            for tag in ('equilibration', 'signal', 'baseline'):
                data = self._gather_data(a, tag)
                writer.writerow([tag.upper()])
                writer.writerow(header)
                writedata(data)
            writer.writerow([])

    def _get_header(self, analysis):
        header = []
        for k in analysis.isotope_keys:
            iso = self._get_isotope(k)
            if iso and iso.header:
                header.extend(iso.header)

        # header = ['{}{}'.format(key, tag) for key in analysis.isotope_keys for tag in ('Time', 'Intensity')]
        header.insert(0, 'COUNTER')
        return header

    def _gather_data(self, a, tag):
        data = []
        for i in a.isotope_keys:
            kiso = self._get_isotope(i)
            if kiso:
                iso = a.get_isotope(i)
                if tag == 'equilibration':
                    iso = iso.sniff
                elif tag == 'baseline':
                    iso = iso.baseline

                if kiso.time:
                    xs = iso.offset_xs
                    data.append(xs)
                if kiso.intensity:
                    ys = iso.ys
                    data.append(ys)

        return zip(*data)

    def _get_isotope(self, k):
        return next((i for i in self.available_isotopes if i.name == k), None)


class Isot(HasTraits):
    name = Str
    intercept_enabled = Bool(True)
    baseline_enabled = Bool(True)
    blank_enabled = Bool(True)
    bs_corrected_enabled = Bool(True)
    bl_corrected_enabled = Bool(True)
    ic_corrected_enabled = Bool(True)
    ic_decay_corrected_enabled = Bool(True)
    ifc_enabled = Bool(True)
    detector_enabled = Bool(True)

    def values(self):
        return (('{}_{}'.format(self.name, tag), getattr(self, '{}_enabled'.format(tag)))
                for tag in ('detector', 'intercept', 'blank', 'baseline', 'bs_corrected',
                            'bl_corrected', 'ic_corrected', 'ic_decay_corrected', 'ifc'))


class CSVAnalysesExportNode(CSVExportNode):
    name = 'Save CSV Analyses'
    available_meta_attributes = List
    selected_meta_attributes = List

    available_ratios = List

    select_all_meta = Button('Select All')
    unselect_all_meta = Button('Unselect All')
    _isotope_klass = Isot

    def traits_view(self):
        cols = [ObjectColumn(name='name', editable=False),
                CheckboxColumn(name='detector_enabled', label='Detector'),
                CheckboxColumn(name='intercept_enabled', label='Intercept'),
                CheckboxColumn(name='baseline_enabled', label='Baseline'),
                CheckboxColumn(name='blank_enabled', label='Blank'),
                CheckboxColumn(name='bs_corrected_enabled', label='Baseline Corrected'),
                CheckboxColumn(name='bl_corrected_enabled', label='Blank Corrected'),
                CheckboxColumn(name='ic_corrected_enabled', label='IC Corrected'),
                CheckboxColumn(name='ic_decay_corrected_enabled', label='IC+Decay Corrected'),
                CheckboxColumn(name='ifc_enabled', label='Interference Corrected')]

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

    def _run_hook(self, writer, analyses):
        header = self._get_header()
        writer.writerow(header)
        for ai in analyses:
            row = self._get_row(header, ai)
            writer.writerow(row)

    def _configure_hook(self):
        self._set_available_isotopes()
        temps = ('lab_temperature', 'east_diffuser_temperature', 'east_return_temperature', 'outside_temperature')
        self.available_meta_attributes = list(('rundate', 'timestamp') + META_ATTRS + EXTRACTION_ATTRS + temps)
        self._select_all_meta_fired()

    def _unselect_all_meta_fired(self):
        self.selected_meta_attributes = []

    def _select_all_meta_fired(self):
        self.selected_meta_attributes = self.available_meta_attributes

    def _get_header(self):
        header = self.selected_meta_attributes[:]

        vargs = [], [], [], [], [], [], [], [], []
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

        def get_ic_decay_corrected(iso):
            return iso.get_ic_decay_corrected_value()

        def get_ifc(iso):
            return iso.get_interference_corrected_value()

        row = []
        for attr in header:
            if attr == 'error':
                continue

            for tag, func in (('intercept', get_intercept),
                              ('blank', get_blank),
                              ('baseline', get_baseline),
                              ('bs_corrected', get_baseline_corrected),
                              ('bl_corrected', get_blank_corrected),
                              ('ic_corrected', get_ic_corrected),
                              ('ic_decay_corrected', get_ic_decay_corrected),
                              ('ifc', get_ifc)):

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
# ============= EOF =============================================
