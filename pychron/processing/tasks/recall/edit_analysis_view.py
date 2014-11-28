# ===============================================================================
# Copyright 2014 Jake Ross
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

#============= enthought library imports =======================
from traits.api import HasTraits, List, on_trait_change, Bool, Event, Float, Str
from traitsui.api import View, UItem, TableEditor, HGroup, spring, Handler, VGroup, Group

#============= standard library imports ========================
#============= local library imports  ==========================
from traitsui.table_column import ObjectColumn
from uncertainties import std_dev, nominal_value, ufloat
from pychron.envisage.icon_button_editor import icon_button_editor


class AnalysisEditViewHandler(Handler):
    def closed(self, info, isok):
        if not isok:
            info.object.revert()
        info.object.clear()


class ICFactor(HasTraits):
    value = Float(auto_set=False, enter_set=True)
    error = Float(auto_set=False, enter_set=True)
    name = Str
    ovalue = Float
    oerror = Float
    dirty = Bool


class AnalysisEditView(HasTraits):
    isotopes = List
    baselines = List
    blanks = List
    ic_factors = List

    revert_button = Event
    dirty = Bool

    control = None
    editor = None

    def __init__(self, editor, *args, **kw):
        super(AnalysisEditView, self).__init__(*args, **kw)
        self.editor = editor
        self.load()

    def load(self):
        m = self.editor.model
        self.title = 'Edit Data - {}'.format(m.record_id)
        self.load_isotopes()

    def load_isotopes(self):
        isos = self.editor.model.isotopes
        ns = []
        bks = []
        bs = []
        ics = []
        dets = []
        for k in self.editor.model.isotope_keys:
            iso = isos[k]
            iso.use_static = True
            ns.append(iso)
            bks.append(iso.blank)
            bs.append(iso.baseline)

            det = iso.detector
            if not det in dets:
                v, e = nominal_value(iso.ic_factor), std_dev(iso.ic_factor)
                ics.append(ICFactor(value=v, error=e,
                                    ovalue=v, oerror=e,
                                    name=det))
            dets.append(det)

        self.isotopes = ns
        self.blanks = bks
        self.baselines = bs
        self.ic_factors = ics

        # self.isotopes = [isos[k] for k in self.editor.model.isotope_keys]

    @on_trait_change('[isotopes,blanks,baselines]:[_value,_error]')
    def _handle_change(self, obj, name, old, new):
        # self.dirty = True
        # obj.dirty = True
        # model = self.editor.model
        # model.calculate_age(force=True)
        # model.analysis_view.main_view.load(model, refresh=True)
        self._set_dirty(obj)
        self._update_model()

    @on_trait_change('ic_factors:[value, error]')
    def _handle_ic_change(self, obj, name, old, new):
        if obj.ovalue == obj.value and obj.oerror == obj.error:
            return

        self._set_dirty(obj)

        v = ufloat(obj.value, obj.error, tag='{} IC'.format(obj.name))
        self._set_ic_factor(obj.name, v)

        self._update_model()

    def _set_ic_factor(self, det, v):
        isos = self.editor.model.isotopes
        for iso in isos.itervalues():
            if iso.detector == det:
                iso.ic_factor = v

    def _set_dirty(self, obj):
        self.dirty = True
        obj.dirty = True

    def _update_model(self):
        model = self.editor.model
        model.calculate_age(force=True)
        model.analysis_view.main_view.load(model, refresh=True)

    def _revert_button_fired(self):
        self.revert()

    def show(self):
        self.control.raise_()

    def clear(self):
        for iso in self.isotopes:
            iso.use_static = False

        self.editor.edit_view = None
        self.control = None

    def revert(self):
        for iso in self.isotopes:
            iso.revert_user_defined()

        for ic in self.ic_factors:
            if ic.dirty:
                v = ufloat(ic.ovalue, ic.oerror, tag='{} IC'.format(ic.name))
                self._set_ic_factor(ic.name, v)
                ic.value = ic.ovalue
                ic.error = ic.oerror
                ic.dirty = False

        self.dirty = False
        self._update_model()

    def traits_view(self):
        cols = [ObjectColumn(name='name', editable=False),
                ObjectColumn(name='value'),
                ObjectColumn(name='error')]

        iso_grp = VGroup(UItem('isotopes',
                               editor=TableEditor(columns=cols,
                                                  sortable=False)),
                         label='Intercepts', show_border=True)

        baseline_grp = VGroup(UItem('baselines',
                                    editor=TableEditor(sortable=False,
                                                       columns=cols)),
                              label='Baselines', show_border=True)

        blank_grp = VGroup(UItem('blanks',
                                 editor=TableEditor(
                                     sortable=False,
                                     columns=cols)),
                           label='Blanks', show_border=True)

        icgrp = VGroup(UItem('ic_factors',
                             editor=TableEditor(
                                 sortable=False,
                                 columns=cols)),
                       label='IC Factors', show_border=True)

        bgrp = HGroup(icon_button_editor('revert_button',
                                         'arrow_undo',
                                         tooltip='Undo changes',
                                         enabled_when='dirty'), spring)
        v = View(VGroup(Group(iso_grp, baseline_grp, icgrp, layout='tabbed'),
                        blank_grp, bgrp),
                 buttons=['OK', 'Cancel'],
                 handler=AnalysisEditViewHandler(),
                 resizable=True,
                 title=self.title,
                 x=0.05,
                 y=0.05)

        return v


# ============= EOF =============================================
