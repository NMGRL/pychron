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
from pyface.confirmation_dialog import confirm
from pyface.constant import YES
from pyface.message_dialog import warning
from traits.api import HasTraits, Float, Enum, Str, Bool, on_trait_change, Property, Button, List, Dict
from traitsui.api import View, Item, UItem, Spring, Label, spring, VGroup, HGroup, EnumEditor, ButtonEditor
from envisage.ui.tasks.preferences_pane import PreferencesPane
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.resources import icon
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper
from pychron.pychron_constants import PLUSMINUS, NULL_STR

LAMBDA_K_ATTRS = ('lambda_e', 'lambda_e_error', 'lambda_b', 'lambda_b_error')
ATM_ATTRS = ('Ar40_Ar36_atm', 'Ar40_Ar36_atm_error', 'Ar40_Ar36_atm_citation',
             'Ar40_Ar38_atm', 'Ar40_Ar38_atm_error', 'Ar40_Ar38_atm_citation')


class DecayConstantEntry(HasTraits):
    name = Str  # ('Steiger & Jager')
    lambda_e = Float  # (5.81e-11)
    lambda_e_error = Float  # (0)
    lambda_b = Float  # (4.962e-10)
    lambda_b_error = Float  # (0)
    total_k_decay = Property(depends_on='lambda_e, lambda_b')

    def _get_total_k_decay(self):
        return self.lambda_e + self.lambda_b

    def totuple(self):
        return tuple([getattr(self, a) for a in LAMBDA_K_ATTRS])

    def traits_view(self):
        v = View(VGroup(Item('name'),
                        HGroup(UItem('lambda_e'), Label(PLUSMINUS), UItem('lambda_e_error'),
                               show_border=True, label='Ar40K epsilon/yr'),
                        HGroup(UItem('lambda_b'), Label(PLUSMINUS), UItem('lambda_b_error'),
                               show_border=True, label='Ar40K beta/yr'),
                        Item('total_k_decay', style='readonly')),
                 buttons=['OK', 'Cancel'],
                 title='Add Decay Constant Entry',
                 kind='livemodal')
        return v


class AtmConstantsEntry(HasTraits):
    name = Str
    Ar40_Ar36_atm = Float
    Ar40_Ar36_atm_error = Float
    Ar40_Ar38_atm = Float
    Ar40_Ar38_atm_error = Float

    def totuple(self):
        return tuple([getattr(self, a) for a in ATM_ATTRS])

    def traits_view(self):
        v = View(VGroup(Item('name'),
                        HGroup(UItem('Ar40_Ar36_atm'), Label(PLUSMINUS), UItem('Ar40_Ar36_atm_err'),
                               show_border=True, label='(Ar40/Ar36)atm'),
                        HGroup(UItem('Ar40_Ar38_atm'), Label(PLUSMINUS), UItem('Ar40_Ar38_atm_err'),
                               show_border=True, label='(Ar40/Ar38)atm')),
                 buttons=['OK', 'Cancel'],
                 title='Add Atm Constant Entry',
                 kind='livemodal')
        return v


class ArArConstantsPreferences(BasePreferencesHelper):
    name = 'Constants'
    preferences_path = 'pychron.arar.constants'
    Ar40_Ar36_atm = Float(295.5)
    Ar40_Ar36_atm_error = Float(0)
    Ar40_Ar38_atm = Float(1575)
    Ar40_Ar38_atm_error = Float(2)
    lambda_e = Float(5.81e-11)
    lambda_e_error = Float(0)
    lambda_b = Float(4.962e-10)
    lambda_b_error = Float(0)
    lambda_Cl36 = Float(6.308e-9)
    lambda_Cl36_error = Float(0)
    lambda_Ar37 = Float(0.01975)
    lambda_Ar37_error = Float(0)
    lambda_Ar39 = Float(7.068e-6)
    lambda_Ar39_error = Float(0)
    Ar37_Ar39_mode = Enum('Normal', 'Fixed')
    Ar37_Ar39 = Float(0.01)
    Ar37_Ar39_error = Float(0.01)
    allow_negative_ca_correction = Bool

    # ===========================================================================
    # spectrometer
    # ===========================================================================
    abundance_sensitivity = Float(0)
    sensitivity = Float(0)
    ic_factor = Float(1.0)
    ic_factor_error = Float(0.0)

    age_units = Enum('Ma', 'ka', 'Ga')

    #citations
    Ar40_Ar36_atm_citation = Str
    Ar40_Ar38_atm_citation = Str
    lambda_e_citation = Str
    lambda_b_citation = Str
    lambda_Cl36_citation = Str
    lambda_Ar37_citation = Str
    lambda_Ar39_citation = Str

    decay_constant_entries = Dict({'Min et al., 2000': (5.80e-11, 0, 4.884e-10, 0),
                                   'Steiger & Jager 1977': (5.81e-11, 0, 4.962e-10, 0)})
    add_decay_constant = Button
    delete_decay_constant = Button
    decay_constant_name = Str(NULL_STR)
    decay_constant_names = List([NULL_STR, 'Min et al., 2000', 'Steiger & Jager 1977'])
    decay_constant_entry_deletable = Property(depends_on='decay_constant_name')
    total_k_decay = Property(depends_on='lambda_e, lambda_b')

    atm_constant_entries = Dict({'Nier 1950': (295.5, 0.5, 'Nier 1950', 1575.0, 2.0, 'Nier 1950'),
                                 'Lee et al., 2006': (
                                     298.56, 0.31, 'Lee et al., 2006', 1583.87, 3.01, 'Lee et al., 2006')})
    atm_constant_name = Str(NULL_STR)
    atm_constant_names = List([NULL_STR, 'Nier 1950', 'Lee et al., 2006'])
    add_atm_constant = Button
    delete_atm_constant = Button
    atm_constant_entry_deletable = Property(depends_on='atm_constant_name')

    def _update_entries(self, new, entries, attrs):
        if new in entries:
            vs = entries[new]
            for a, v in zip(attrs, vs):
                setattr(self, a, v)

    def _find_entry(self, entries, attrs):

        def test_entry(v):
            return all([getattr(self, attr) == pvalue
                        for attr, pvalue in zip(attrs, v)])

        return next((k for k, v in entries.iteritems() if test_entry(v)), NULL_STR)

    def _find_decay_constant_entry(self):
        return self._find_entry(self.decay_constant_entries, LAMBDA_K_ATTRS)

    def _find_atm_constant_entry(self):
        return self._find_entry(self.atm_constant_entries, ATM_ATTRS)

    # handlers
    def _delete_atm_constant_fired(self):
        dn = self.atm_constant_name
        result = confirm(None, 'Are you sure you want to remove "{}"'.format(dn))
        if result == YES:
            self.atm_constant_names.remove(dn)
            self.atm_constant_entries.pop(dn)
            self.atm_constant_name = self.atm_constant_names[-1] if self.atm_constant_names else NULL_STR

    def _delete_decay_constant_fired(self):
        dn = self.decay_constant_name
        result = confirm(None, 'Are you sure you want to remove "{}"'.format(dn))
        if result == YES:
            self.decay_constant_names.remove(dn)
            self.decay_constant_entries.pop(dn)
            self.decay_constant_name = self.decay_constant_names[-1] if self.decay_constant_names else NULL_STR

    def _add_atm_constant_fired(self):
        e = AtmConstantsEntry()
        for a in ATM_ATTRS:
            setattr(e, a, getattr(self, a))

        info = e.edit_traits()
        name = e.name
        if info.result and name:
            if name not in self.atm_constant_names:
                nv = e.totuple()
                exists = next((k for k, v in self.atm_constant_entries.iteritems() if nv == v), None)
                if exists:
                    warning(None,
                            'Atm constant entry with those values already exists.\nExisting entry named "{}"'.format(
                                exists))
                else:
                    self.atm_constant_names.append(name)
                    self.atm_constant_entries[name] = e.totuple()
                    self.atm_constant_name = name
            else:
                warning(None, 'Atm constant entry with that name alreay exists')

    def _add_decay_constant_fired(self):
        e = DecayConstantEntry()
        for a in LAMBDA_K_ATTRS:
            setattr(e, a, getattr(self, a))

        info = e.edit_traits()
        name = e.name
        if info.result and name:
            if name not in self.decay_constant_names:
                nv = e.totuple()
                exists = next((k for k, v in self.decay_constant_entries.iteritems() if nv == v), None)
                if exists:
                    warning(None,
                            'Decay constant entry with those values already exists.\nExisting entry named "{}"'.format(
                                exists))
                else:
                    self.decay_constant_names.append(name)
                    self.decay_constant_entries[name] = e.totuple()
                    self.decay_constant_name = name
            else:
                warning(None, 'Decay constant entry with that name alreay exists')

    def _decay_constant_name_changed(self, new):
        self._update_entries(new, self.decay_constant_entries, LAMBDA_K_ATTRS)

    def _atm_constant_name_changed(self, new):
        self._update_entries(new, self.atm_constant_entries, ATM_ATTRS)

    @on_trait_change('Ar40_Ar36_atm,Ar40_Ar36_atm_error,Ar40_Ar38_atm, Ar40_Ar38_atm_error')
    def _decay_constants_change(self):
        d = self._find_atm_constant_entry()
        self.atm_constant_name = d

    @on_trait_change('lambda_e,lambda_e_error,lambda_b,lambda_b_error')
    def _decay_constants_change(self):
        d = self._find_decay_constant_entry()
        self.decay_constant_name = d

    def _get_total_k_decay(self):
        return self.lambda_e + self.lambda_b

    def _set_total_k_decay(self, v):
        pass

    def _get_decay_constant_entry_deletable(self):
        return self.decay_constant_name not in (NULL_STR, 'Min et al., 2000', 'Steiger & Jager 1977')

    def _get_atm_constant_entry_deletable(self):
        return self.atm_constant_name not in (NULL_STR, 'Lee et al., 2006', 'Nier 1950')

    def _set_atm_constant_entry_deletable(self, v):
        pass

    def _set_decay_constant_entry_deletable(self, v):
        pass

    def _get_value(self, name, value):
        if name == 'total_k_decay':
            return self._get_total_k_decay()
        elif name in ('decay_constant_entry_deletable','atm_constant_entry_deletable'):
            pass
        else:
            return super(ArArConstantsPreferences, self)._get_value(name, value)


class ArArConstantsPreferencesPane(PreferencesPane):
    category = 'Constants'
    model_factory = ArArConstantsPreferences

    def _get_decay_group(self):
        presets = HGroup(Item('decay_constant_name', editor=EnumEditor(name='decay_constant_names')),
                         UItem('add_decay_constant',
                               tooltip='add decay constant entry',
                               style='custom',
                               editor=ButtonEditor(image=icon('add'))),
                         UItem('delete_decay_constant',
                               tooltip='delete current constant entry',
                               enabled_when='decay_constant_entry_deletable',
                               style='custom',
                               editor=ButtonEditor(image=icon('delete'))))

        vs = [
            ('Ar40K epsilon/yr', 'lambda_e', 'lambda_e_error'),
            ('Ar40K beta/yr', 'lambda_b', 'lambda_b_error'),
            ('Cl36/d', 'lambda_Cl36', 'lambda_Cl36_error'),
            ('Ar37/d', 'lambda_Ar37', 'lambda_Ar37_error'),
            ('Ar39/d', 'lambda_Ar39', 'lambda_Ar39_error')]
        items = [HGroup(Label(l), spring, UItem(v), UItem(e)) for l, v, e in vs]
        decay = VGroup(
            presets,
            HGroup(Item('total_k_decay', style='readonly', label='Total Ar40K')),
            HGroup(spring, Label('Value'),
                   Spring(width=75, springy=False),
                   Label(u'{}1s'.format(PLUSMINUS)),
                   Spring(width=75, springy=False)),
            *items,
            show_border=True,
            label='Decay')
        return decay

    def _get_ratio_group(self):
        presets = HGroup(Item('atm_constant_name', editor=EnumEditor(name='atm_constant_names')),
                         UItem('add_atm_constant',
                               tooltip='add atm constant entry',
                               style='custom',
                               editor=ButtonEditor(image=icon('add'))),
                         UItem('delete_atm_constant',
                               tooltip='delete current constant entry',
                               enabled_when='atm_constant_entry_deletable',
                               style='custom',
                               editor=ButtonEditor(image=icon('delete'))))
        ratios = VGroup(
            presets,
            HGroup(Spring(springy=False, width=125),
                   Label('Value'),
                   Spring(springy=False, width=55),
                   Label(u'{}1s'.format(PLUSMINUS)),
                   Spring(springy=False, width=55),
                   Label('Citation')),
            HGroup(Item('Ar40_Ar36_atm', label='(40Ar/36Ar)atm'),
                   Item('Ar40_Ar36_atm_error', show_label=False),
                   Item('Ar40_Ar36_atm_citation', show_label=False)),
            HGroup(Item('Ar40_Ar38_atm', label='(40Ar/38Ar)atm'),
                   Item('Ar40_Ar38_atm_error', show_label=False),
                   Item('Ar40_Ar38_atm_citation', show_label=False)),
            Item('_'),
            HGroup(
                Item('Ar37_Ar39_mode', label='(37Ar/39Ar)K'),
                Item('Ar37_Ar39', show_label=False),
                Item('Ar37_Ar39_error', show_label=False)),
            label='Ratios')
        return ratios

    def traits_view(self):
        ratios = self._get_ratio_group()
        decay = self._get_decay_group()
        spectrometer = VGroup(
            Item('abundance_sensitivity'),
            Item('sensitivity',
                 tooltip='Nominal spectrometer sensitivity saved with analysis'),
            label='Spectrometer')

        general = VGroup(Item('age_units', label='Age Units'),
                         Item('allow_negative_ca_correction',
                              tooltip='If checked Ca36 can be negative when correcting Ar36 for Ca inteference',
                              label='Allow Negative Ca Correction'),
                         label='General')

        v = View(general, decay, ratios, spectrometer)
        return v
        # ============= EOF =============================================