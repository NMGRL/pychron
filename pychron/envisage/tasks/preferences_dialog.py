# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from envisage.ui.tasks.preferences_category import PreferencesCategory
from envisage.ui.tasks.preferences_dialog import PreferencesDialog, PreferencesTab
from pyface.tasks.topological_sort import before_after_sort
from traitsui.api import View, ListStrEditor, \
    UItem, HSplit
from traits.api import on_trait_change, List, Str
# ============= standard library imports ========================
# ============= local library imports  ==========================


class myPreferencesDialog(PreferencesDialog):
    names = List
    selected = Str

    def traits_view(self):
        buttons = ['OK', 'Cancel']
        if self.show_apply:
            buttons = ['Apply'] + buttons

        v = View(
            HSplit(
                UItem('names',
                      editor=ListStrEditor(
                          selected='selected',
                          editable=False,
                      ),
                      width=0.25
                ),
                UItem('_selected',
                      style='custom',
                      width=0.75
                )
            ),
            width=600,
            height=400,
            resizable=True,
            buttons=buttons,
            title='Preferences',
            kind='livemodal'
        )
        return v

    def apply(self, info=None):
        """ Handles the Apply button being clicked.
        """
        for tab in self._tabs:
            for pane in tab.panes:
                try:
                    pane.apply()
                except BaseException:
                    print pane

                    #self.names=[]
                    #self._update_tabs()
                    #info.dispose()


    def _selected_changed(self):
        name = self.selected
        t = next((tab for tab in self._tabs if tab.name == name))
        self._selected = t

    @on_trait_change('categories, panes')
    def _update_tabs(self):
        # Build a { category id -> [ PreferencePane ] } map.
        categories = self.categories[:]
        category_map = dict((category.id, []) for category in categories)
        for pane in self.panes:
            if pane.category in category_map:
                category_map[pane.category].append(pane)
            else:
                categories.append(PreferencesCategory(id=pane.category))
                category_map[pane.category] = [pane]

        # Construct the appropriately sorted list of preference tabs.
        tabs = []
        names = []
        for category in before_after_sort(categories):
            panes = before_after_sort(category_map[category.id])
            tabs.append(PreferencesTab(name=category.name, panes=panes))
            names.append(category.name)

        self._tabs = tabs
        self.names = names


# ============= EOF =============================================
