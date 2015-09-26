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

# ============= enthought library imports =======================
from traits.api import HasTraits, List, on_trait_change, Bool, Event, Float, Str, Instance
from traitsui.api import View, UItem, TableEditor, HGroup, spring, Handler, VGroup, Group, Label
from traitsui.table_column import ObjectColumn

# ============= standard library imports ========================
# ============= local library imports  ==========================
from uncertainties import std_dev, nominal_value, ufloat
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.pychron_constants import PLUSMINUS


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


class EditItem(HasTraits):
    value = Float(auto_set=False, enter_set=True)
    error = Float(auto_set=False, enter_set=True)
    name = Str
    dirty = Bool
    recalculate_needed = Event
    _suppress_update = Bool

    def __init__(self, item, *args, **kw):
        self.item = item
        self.item._ovalue = item.value
        self.item._oerror = item.error

        self.trait_setq(value=item.value, error=item.error, name=item.name)

        super(EditItem, self).__init__(*args, **kw)

    def _value_changed(self, new):
        if self._suppress_update:
            return

        self.item._ovalue = self.item.value
        self.item.value = new
        self.recalculate_needed = True

    def _error_changed(self, new):
        if self._suppress_update:
            return

        self.item._oerror = self.item.error
        self.item.error = new
        self.recalculate_needed = True

    def revert(self):
        item = self.item
        item.revert_user_defined()
        self._suppress_update = True
        self.trait_set(value=item.value, error=item.error)
        self._suppress_update = False


class FluxItem(HasTraits):
    value = Float(auto_set=False, enter_set=True)
    error = Float(auto_set=False, enter_set=True)
    ovalue = Float
    oerror = Float
    dirty = Bool
    recalculate_needed = Event
    _suppress_update = Bool

    def __init__(self, item, *args, **kw):
        self.item = item
        self.ovalue = j = nominal_value(item.j)
        self.oerror = e = std_dev(item.j)

        self.trait_setq(value=j, error=e)

        super(FluxItem, self).__init__(*args, **kw)

    @on_trait_change('value, error')
    def _value_changed(self, new):
        if self._suppress_update:
            return

        self.item.j = ufloat(self.value, self.error, tag='j')
        self.recalculate_needed = True

    def revert(self):
        item = self.item
        item.j = ufloat(self.ovalue, self.oerror, tag='j')
        self._suppress_update = True
        self.trait_set(value=self.ovalue, error=self.oerror)
        self._suppress_update = False


class AnalysisEditView(HasTraits):
    isotopes = List
    baselines = List
    blanks = List
    ic_factors = List

    flux = Instance(FluxItem)

    revert_button = Event
    dirty = Bool

    control = None
    editor = None

    def __init__(self, editor, *args, **kw):
        super(AnalysisEditView, self).__init__(*args, **kw)
        self.editor = editor
        analysis = self.editor.analysis
        self.title = 'Edit Data - {}'.format(analysis.record_id)

        isos = analysis.isotopes
        ns = []
        bks = []
        bs = []
        ics = []
        dets = []
        for k in analysis.isotope_keys:
            iso = isos[k]
            # iso.use_static = True

            eiso = EditItem(iso)
            ns.append(eiso)

            blank = EditItem(iso.blank)
            bks.append(blank)

            baseline = EditItem(iso.baseline)
            bs.append(baseline)

            det = iso.detector
            if det not in dets:
                v, e = nominal_value(iso.ic_factor), std_dev(iso.ic_factor)
                ics.append(ICFactor(value=v, error=e,
                                    ovalue=v, oerror=e,
                                    name=det))
            dets.append(det)

        self.isotopes = ns
        self.blanks = bks
        self.baselines = bs
        self.ic_factors = ics

        self.flux = FluxItem(analysis)

    # @on_trait_change('[isotopes,blanks,baselines]:[value,error]')
    @on_trait_change('[isotopes,blanks,baselines, flux]:recalculate_needed')
    def _handle_change(self, obj, name, old, new):
        # self.dirty = True
        # obj.dirty = True
        # model = self.editor.analysis
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
        isos = self.editor.analysis.isotopes
        for iso in isos.itervalues():
            if iso.detector == det:
                iso.ic_factor = v

    def _set_dirty(self, obj):
        self.dirty = True
        obj.dirty = True

    def _update_model(self):
        model = self.editor.analysis
        model.calculate_age(force=True)
        model.analysis_view.main_view.refresh_needed = True

    def _revert_button_fired(self):
        self.revert()

    def show(self):
        self.control.raise_()

    def clear(self):
        # for iso in self.isotopes:
        # iso.use_static = False

        self.editor.edit_view = None
        self.control = None

    def revert(self):
        if not self.dirty:
            return

        for iso in self.isotopes:
            iso.revert()

        for ic in self.ic_factors:
            if ic.dirty:
                v = ufloat(ic.ovalue, ic.oerror, tag='{} IC'.format(ic.name))
                self._set_ic_factor(ic.name, v)
                ic.value = ic.ovalue
                ic.error = ic.oerror
                ic.dirty = False

        self.flux.revert()

        self.dirty = False
        self._update_model()

    def traits_view(self):
        cols = [ObjectColumn(name='name', editable=False),
                ObjectColumn(name='value', format='%0.7f', width=100),
                ObjectColumn(name='error', format='%0.7f', width=100)]

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
        flux_grp = HGroup(UItem('object.flux.value'),
                          Label(PLUSMINUS),
                          UItem('object.flux.error'),
                          label='Flux (J)',
                          show_border=True)
        v = View(VGroup(Group(iso_grp, baseline_grp, icgrp, layout='tabbed'),
                        blank_grp,
                        flux_grp,
                        bgrp),
                 buttons=['OK', 'Cancel'],
                 handler=AnalysisEditViewHandler(),
                 resizable=True,
                 title=self.title,
                 x=0.05,
                 y=0.05)

        return v

# ============= EOF =============================================
