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
from traits.api import Float, Enum, Str
from traitsui.api import View, Item, UItem, Spring, Label, spring, VGroup, HGroup
from envisage.ui.tasks.preferences_pane import PreferencesPane

from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper
from pychron.pychron_constants import PLUSMINUS



#============= standard library imports ========================
#============= local library imports  ==========================

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

    #===========================================================================
    # spectrometer
    #===========================================================================
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


class ArArConstantsPreferencesPane(PreferencesPane):
    category = 'Constants'
    model_factory = ArArConstantsPreferences

    def _get_decay_group(self):
        vs = [
            ('Ar40K epsilon/yr', 'lambda_e', 'lambda_e_error'),
            ('Ar40K beta/yr', 'lambda_b', 'lambda_b_error'),
            ('Cl36/d', 'lambda_Cl36', 'lambda_Cl36_error'),
            ('Ar37/d', 'lambda_Ar37', 'lambda_Ar37_error'),
            ('Ar39/d', 'lambda_Ar39', 'lambda_Ar39_error'),
        ]
        decay = VGroup(
            *[
                 HGroup(spring, Label('Value'),
                        Spring(width=75, springy=False),
                        Label(u'{}1s'.format(PLUSMINUS)),
                        Spring(width=75, springy=False),
                 )
             ] + \
             [HGroup(Label(l), spring, UItem(v), UItem(e))
              for l, v, e in vs],

            show_border=True,
            label='Decay'
        )
        return decay

    def traits_view(self):
        ratios = VGroup(
            HGroup(Spring(springy=False, width=125),
                   Label('Value'),
                   Spring(springy=False, width=55),
                   Label(u'{}1s'.format(PLUSMINUS)),
                   Spring(springy=False, width=55),
                   Label('Citation')),
            HGroup(Item('Ar40_Ar36_atm', label='(40Ar/36Ar)atm'),
                   Item('Ar40_Ar36_atm_error', show_label=False),
                   Item('Ar40_Ar36_atm_citation', show_label=False)
            ),
            HGroup(Item('Ar40_Ar38_atm', label='(40Ar/38Ar)atm'),
                   Item('Ar40_Ar38_atm_error', show_label=False),
                   Item('Ar40_Ar38_atm_citation', show_label=False)),
            Item('_'),
            HGroup(
                Item('Ar37_Ar39_mode', label='(37Ar/39Ar)K'),
                Item('Ar37_Ar39', show_label=False),
                Item('Ar37_Ar39_error', show_label=False)),
            label='Ratios')

        decay = self._get_decay_group()
        spectrometer = VGroup(
            Item('abundance_sensitivity'),
            Item('sensitivity',
                 tooltip='Nominal spectrometer sensitivity saved with analysis'
            ),
            label='Spectrometer',
            #show_border=True
        )

        general = VGroup(Item('age_units', label='Age Units'),
                         label='General')

        v = View(general, decay, ratios, spectrometer)
        return v

        #============= EOF =============================================
        #         decay = VGroup(
        #                         HGroup(Spring(springy=False, width=125),
        #                                Label('Value'), Spring(springy=False, width=55),
        #                                Label(u'{}1s'.format(PLUSMINUS))),
        #                         HGroup(
        #                                spring,
        #                                Label('Value'),
        # #                                Spring(springy=False, width=55),
        #                                Label(u'{}1s'.format(PLUSMINUS))),

        #                         grp,
        #                         HGroup(Label('Cl36/d')),
        #                         HGroup(Label('Ar37/d')),
        #                         HGroup(Label('Ar39/d')),
        #                         HGroup(
        #                                 VGroup(
        # #                                        spring,
        #                                        HGroup(spring, Label('Ar40K epsilon/yr')),
        # #                                        spring,
        #                                        HGroup(spring, Label('Ar40K beta/yr')),
        # #                                        spring,
        #                                        HGroup(spring, Label('Cl36/d')),
        # #                                        spring,
        #                                        HGroup(spring, Label('Ar37/d')),
        # #                                        spring,
        #                                        HGroup(spring, Label('Ar39/d')),
        #                                        ),
        #                                 VGroup(
        #                                        HGroup(Item('lambda_e',),
        #                                               Item('lambda_e_error'), show_labels=False),
        #                                        HGroup(Item('lambda_b'),
        #                                               Item('lambda_b_error'), show_labels=False),
        #                                        HGroup(Item('lambda_Cl36'),
        #                                               Item('lambda_Cl36_error'), show_labels=False),
        #                                        HGroup(Item('lambda_Ar37'),
        #                                               Item('lambda_Ar37_error'), show_labels=False),
        #                                        HGroup(Item('lambda_Ar39'),
        #                                               Item('lambda_Ar39_error'), show_labels=False)
        #                                        )
        #                                ),
        #                         show_border=True,
        #                         label='Decay'
        #                         )