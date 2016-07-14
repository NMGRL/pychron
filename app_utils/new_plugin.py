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
import os


# ============= standard library imports ========================
# ============= local library imports  ==========================

def make_pkg(root):
    os.mkdir(root)
    with open(os.path.join(root, '__init__.py'), 'w') as wfile:
        wfile.write(BOILER_PLATE.format(''))


def make_file(root, name, txt):
    with open(os.path.join(root, name), 'w') as wfile:
        wfile.write(BOILER_PLATE.format(txt))


def new_plugin(root, options):
    # with open(os.path.join(root))
    make_pkg(root)

    troot = os.path.join(root, 'tasks')
    make_pkg(troot)

    make_file(troot, 'plugin.py', options['plugin_txt'])

    make_file(troot, 'panes.py', options['panes_txt'])
    make_file(troot, 'actions.py', options['actions_txt'])
    make_file(troot, 'preferences.py', options['preferences_txt'])
    make_file(troot, 'task.py', options['task_txt'])


BOILER_PLATE = '''# ===============================================================================
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
from traits.api import List, Int, HasTraits, Str, Bool
from traitsui.api import View, UItem, Item, HGroup, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
{}
# ============= EOF =============================================
'''

TASK_TXT = '''
from pyface.tasks.task_layout import TaskLayout, PaneItem
class FurnaceTask(BaseManagerTask):
    id = 'pychron.furnace.task'
    def activated(self):
        pass

    def prepare_destroy(self):
        pass

    def create_dock_panes(self):
        return []

    def create_central_pane(self):
        pass

    def _default_layout_default(self):
        return TaskLayout()
'''

PANES_TXT = '''
from traitsui.api import View, UItem, Item, VGroup, HGroup
from pyface.tasks.traits_task_pane import TraitsTaskPane
from pyface.tasks.traits_dock_pane import TraitsDockPane

'''

ACTIONS_TXT = '''
'''

PREF_TXT = '''
from envisage.ui.tasks.preferences_pane import PreferencesPane
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper

class NMGRLFurnacePreferences(BasePreferencesHelper):
    pass


class NMGRLFurnacePreferencesPane(PreferencesPane):
    category = 'NMGRL Furnace'
    model_factory = NMGRLFurnacePreferences

    def traits_view(self):
        v = View()
        return v

'''
PLUGIN_TXT = '''
from envisage.ui.tasks.task_extension import TaskExtension
from envisage.ui.tasks.task_factory import TaskFactory
from pyface.tasks.action.schema_addition import SchemaAddition


from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin

class BaseFurnacePlugin(BaseTaskPlugin):
    id = 'pychron.furnace.base.plugin'
    managers = List(contributes_to='pychron.hardware.managers')
    klass = None

    def _manager_factory(self):
        """
        """
        m = self.klass()
        m.bootstrap()
        m.plugin_id = self.id
        m.bind_preferences(self.id)

        return m

    def _task_factory(self):
        pass

    def _managers_default(self):
        """
        """
        d = []

        if self.klass is not None:
            d = [dict(name=self.name,
                      plugin_name=self.name,
                      manager=self.application.get_service(IFurnaceManager, 'name=="{}"'.format(self.name)))]

        return d

    def _service_offers_default(self):
        """
        """
        # so = self.service_offer_factory()
        return []

    # def _preferences_default(self):
    #     return ['file://{}'.format('')]
    #
    # def _task_extensions_default(self):
    #
    #     return [TaskExtension(SchemaAddition)]

    def _tasks_default(self):
        return [TaskFactory(factory=self._task_factory,
                            protocol=FurnaceTask)]

class NMGRLFurnacePlugin(BaseFurnacePlugin):
    id = 'pychron.furnace.nmgrl.plugin'

    klass = 'pychron.furnace.nmgrl_furnace.NMGRLFurnaceManager'

    def _preferences_panes_default(self):
        return [NMGRLFurnacePreferencesPane]
'''

if __name__ == '__main__':
    root = '/Users/ross/Programming/github/pychron_dev/pychron/furnace'
    # root = '/Users/ross/Sandbox/furnace'

    options = {'plugin_txt': PLUGIN_TXT, 'panes_txt': PANES_TXT,
               'actions_txt': ACTIONS_TXT, 'preferences_txt': PREF_TXT,
               'task_txt': TASK_TXT}
    new_plugin(root, options)


# ============= EOF =============================================
