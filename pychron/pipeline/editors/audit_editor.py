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
from traits.api import HasTraits, List, Any, Instance, Bool, Set, Event, Int
from traitsui.api import TabularEditor, View, Item, UItem, HGroup, VGroup
from traitsui.tabular_adapter import TabularAdapter

from pychron.core.helpers.isotope_utils import sort_isotopes, sort_detectors
from pychron.envisage.tasks.base_editor import BaseTraitsEditor


class AuditAdapter(TabularAdapter):
    columns = [('RunID', 'record_id'),
               ('Date', 'rundate'),
               ]
    font = '10'
    width = Int(70)

    def set_columns(self, isos, dets):
        cs = [('RunID', 'record_id'),
              ('Date', 'rundate')]
        for i in sort_isotopes(isos):
            for k in ('rev.', 'fit', 'bs. fit'):
                cs.append(('{} {}'.format(i, k), 'iso:{}:{}'.format(k, i)))

        for d in sort_detectors(dets):
            for k in ('rev.',):
                cs.append(('{} IC {}'.format(d, k), 'ic:{}:{}'.format(k, d)))

        self.columns = cs

    def get_width(self, obj, trait, column):
        if column == 1:
            return 110
        elif column == 0:
            return 60
        else:
            return super(AuditAdapter, self).get_width(obj, trait, column)

    def _get_ic_text(self, name):
        ret = ''
        _, kind, det = name.split(':')
        iso = self.item.get_isotope(detector=det)

        if kind == 'rev.':
            ret = 'Yes' if iso.ic_factor_reviewed else 'No'
        return ret

    def _get_iso_text(self, name):
        ret = ''
        _, kind, iso = name.split(':')
        iso = self.item.get_isotope(iso)
        if kind == 'rev.':
            ret = 'Yes' if iso.reviewed else 'No'
        elif kind == 'fit':
            ret = iso.fit_abbreviation
        elif kind == 'bs. fit':
            ret = iso.baseline.fit_abbreviation
        return ret

    def get_text(self, obj, trait, row, column):
        name = self.column_map[column]

        if name.startswith('iso:'):
            ret = self._get_iso_text(name)
        elif name.startswith('ic:'):
            ret = self._get_ic_text(name)
        else:
            ret = super(AuditAdapter, self).get_text(obj, trait, row, column)

        return ret


class AuditEditor(BaseTraitsEditor):
    unknowns = List
    references = List
    selected = Any
    adapter = Instance(AuditAdapter, ())
    isotopes = Set
    detectors = Set
    hide_reviewed = Bool(True)

    def _hide_reviewed_changed(self, new):
        if new:
            isos = [iso for iso in self.isotopes if
                    not all(a.get_isotope(iso).reviewed for ans in (self.unknowns, self.references) for a in ans)]
            dets = self.detectors
        else:
            isos = self.isotopes
            dets = self.detectors

        self.adapter.set_columns(isos, dets)

    def set_columns(self, unks, refs):
        isos = {k for ans in (unks, refs) for ai in ans for k in ai.isotope_keys}
        dets = {v.detector for ans in (unks, refs) for ai in ans for v in ai.itervalues()}

        self.isotopes = isos
        self.detectors = dets

        self._hide_reviewed_changed(self.hide_reviewed)

    def set_unks_refs(self, unks, refs):
        self.unknowns = unks
        self.references = refs

        self.set_columns(unks, refs)

    def traits_view(self):
        tools_grp = HGroup(Item('hide_reviewed'))
        unk_grp = UItem('unknowns', editor=TabularEditor(selected='selected',
                                                         editable=False,
                                                         stretch_last_section=False,
                                                         adapter=self.adapter))

        v = View(VGroup(tools_grp, unk_grp))
        return v

# ============= EOF =============================================
