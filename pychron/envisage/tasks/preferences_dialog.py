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
from envisage.ui.tasks.preferences_category import PreferencesCategory
from envisage.ui.tasks.preferences_dialog import PreferencesDialog as PD, PreferencesTab
from pyface.tasks.topological_sort import before_after_sort
from traitsui.api import View, UItem
from traitsui.group import HGroup
from traits.api import on_trait_change, Property
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter
from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.envisage.resources import icon

ICON_MAP = {'Database': icon('database'),
            'Social': icon('edit-group'),
            'Experiment': icon('applications-science_32'),
            'Console': icon('openterm'),
            'Processing': icon('tools-anvil'),
            'Update': icon('update_misc'),
            'General': icon('go-home-5'),
            'Spectrometer': icon('spectrum_emission'),
            # 'Hardware': icon('speedometer'),
            'DVC': icon('git'),
            'Pipeline': icon('pipe'),
            'Hardware': icon('toolbox'),
            'Constants': icon('applications-education-mathematics'),
            'Labspy': icon('labspy'),
            'Fusions Diode': icon('laser'),
            'Fusions UV': icon('laser'),
            'Fusions CO2': icon('laser'),
            'ExtractionLine': icon('motherboard'),
            'ClientExtractionLine': icon('motherboard'),
            'Entry': icon('radioactivity'),
            'Loading': icon('caterpillar'),
            'Scripts': icon('scripts_text'),
            'Dashboard': icon('dashboard'),
            'SystemMonitor': icon('action_log')}


class CatergoryAdapter(TabularAdapter):
    columns = [('Category', 'name')]
    name_image = Property
    font = 'helvetica 14'

    def _get_name_image(self):
        return ICON_MAP.get(self.item.name)


class PreferencesDialog(PD):
    @on_trait_change('categories, panes')
    def _update_tabs(self):
        # Build a { category id -> [ PreferencePane ] } map.
        categories = self.categories[:]
        category_map = dict((category.id, []) for category in categories)
        for pane in self.panes:

            # force pane to call trait_context
            # for some reason when using this PreferencesDialog
            # pane._model is None (only set when trait_context called)
            pane.trait_context()

            if pane.category in category_map:
                category_map[pane.category].append(pane)
            else:
                categories.append(PreferencesCategory(id=pane.category))
                category_map[pane.category] = [pane]

        # Construct the appropriately sorted list of preference tabs.
        tabs = []
        for category in before_after_sort(categories):
            panes = before_after_sort(category_map[category.id])
            tabs.append(PreferencesTab(name=category.name, panes=panes))
        self._tabs = tabs

        # auto select first category
        self._selected = tabs[0]

    def traits_view(self):

        a = UItem('_tabs', width=-200,
                  editor=myTabularEditor(adapter=CatergoryAdapter(),
                                         row_height=32,
                                         editable=False,
                                         horizontal_lines=False,
                                         selected='_selected'))
        b = UItem('_selected', style='custom')
        v = View(HGroup(a, b),
                 height=500,
                 width=800,
                 kind='livemodal',
                 title='Preferences',
                 resizable=True,
                 buttons=['OK', 'Cancel'])
        return v

        # ============= EOF =============================================
        # cols = [ObjectColumn(name='name',
        # width=104,
        # label='Category'),
        # ObjectColumn(name='image',
        # label='image',
        # width=20)]
        # cat_grp = UItem('_tabs',
        # width=-125,
        # editor=TableEditor(columns=cols,
        # editable=False,
        # sortable=False,
        # selected='_selected')

        # v = View(HGroup(,
        # UItem('_selected',
        # style='custom')),
        #     height = 500,
        #              width = 800,
        #                      kind = 'livemodal',
        #                             title = 'Preferences',
        #                                     resizable = True,
        #                                                 buttons = ['OK', 'Cancel'])
        # class myPreferencesDialog(PreferencesDialog):
        # names = List
        # selected = Str
        #
        # def traits_view(self):
        # buttons = ['OK', 'Cancel']
        # if self.show_apply:
        # buttons = ['Apply'] + buttons
        #
        # v = View(
        # HSplit(
        # UItem('names',
        # editor=ListStrEditor(
        # selected='selected',
        #                           editable=False,
        #                       ),
        #                       width=0.25
        #                 ),
        #                 UItem('_selected',
        #                       style='custom',
        #                       width=0.75
        #                 )
        #             ),
        #             width=600,
        #             height=400,
        #             resizable=True,
        #             buttons=buttons,
        #             title='Preferences',
        #             kind='livemodal'
        #         )
        #         return v
        #
        #     def apply(self, info=None):
        #         """ Handles the Apply button being clicked.
        #         """
        #         for tab in self._tabs:
        #             for pane in tab.panes:
        #                 try:
        #                     pane.apply()
        #                 except BaseException:
        #                     print pane
        #
        #                     #self.names=[]
        #                     #self._update_tabs()
        #                     #info.dispose()
        #
        #
        #     def _selected_changed(self):
        #         name = self.selected
        #         t = next((tab for tab in self._tabs if tab.name == name))
        #         self._selected = t
        #
        #     @on_trait_change('categories, panes')
        #     def _update_tabs(self):
        #         # Build a { category id -> [ PreferencePane ] } map.
        #         categories = self.categories[:]
        #         category_map = dict((category.id, []) for category in categories)
        #         for pane in self.panes:
        #             if pane.category in category_map:
        #                 category_map[pane.category].append(pane)
        #             else:
        #                 categories.append(PreferencesCategory(id=pane.category))
        #                 category_map[pane.category] = [pane]
        #
        #         # Construct the appropriately sorted list of preference tabs.
        #         tabs = []
        #         names = []
        #         for category in before_after_sort(categories):
        #             panes = before_after_sort(category_map[category.id])
        #             tabs.append(PreferencesTab(name=category.name, panes=panes))
        #             names.append(category.name)
        #
        #         self._tabs = tabs
        #         self.names = names
