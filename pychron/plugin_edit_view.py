# ===============================================================================
# Copyright 2014 Jake Ross
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
from traits.api import HasTraits, Str, Bool, List, Event, Instance
from pyface.confirmation_dialog import confirm
from pyface.action.menu_manager import MenuManager
from traitsui.menu import Action
from traitsui.api import View, UItem, Handler
from traitsui.tree_node import TreeNode
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.ui.tree_editor import TreeEditor
from pychron.envisage.resources import icon
from pychron.core.helpers.filetools import to_bool
from pychron.initialization_parser import InitializationParser


class gTreeNode(TreeNode):
    def get_icon(self, object, is_expanded):
        if object.enabled:
            return icon('add')
        else:
            return icon('delete')


class Plugin(HasTraits):
    name = Str
    enabled = Bool


class PluginTree(Plugin):
    plugins = List(Plugin)


class PEVHandler(Handler):
    def set_enabled(self, info, obj):
        obj.enabled = True
        info.object.update()

    def set_disabled(self, info, obj):
        obj.enabled = False
        info.object.update()


class PluginEditView(HasTraits):
    plugin_tree = PluginTree
    refresh_needed = Event
    _parser = Instance(InitializationParser)

    def save(self):
        self._parser.save()

    def update(self):
        ip = self._parser
        for pt in self.plugin_tree.plugins:
            for plugin in pt.plugins:
                # print plugin.name, plugin.enabled
                if plugin.enabled:
                    ip.enable_plugin(plugin.name, pt.name.lower(), save=False)
                else:
                    ip.disable_plugin(plugin.name, save=False)
        # ip.save()
        self.refresh_needed = True

    def traits_view(self):
        nodes = [
            TreeNode(node_for=[PluginTree],
                     auto_open=True,
                     children='plugins',
                     label='name'),
            gTreeNode(node_for=[Plugin],
                      menu=MenuManager(Action(name='Enable',
                                              action='set_enabled',
                                              visible_when='not object.enabled'),
                                       Action(name='Disable',
                                              visible_when='object.enabled',
                                              action='set_disabled')),
                      label='name')]
        v = View(UItem('plugin_tree', editor=TreeEditor(nodes=nodes,
                                                        editable=False,
                                                        refresh_icons='refresh_needed')),
                 title='Edit Plugins',
                 handler=PEVHandler(),
                 height=600,
                 width=400,
                 kind='livemodal',
                 buttons=['OK', 'Cancel'],
                 resizable=True)
        return v


def load_tree():
    p = PluginTree(name='Plugins')
    plugins = []
    for name, ps in (('General', ('Experiment', 'PyScript',
                                  'ArArConstants', 'Loading',
                                  'Processing', 'Database',
                                  'Entry', 'SystemMonitor',
                                  'Workspace', 'LabBook')),
                     ('Hardware', ('ArgusSpectrometer', 'ExtractionLine',
                                   'FusionsCO2', 'FusionsDiode', 'FusionsUV',
                                   'ExternalPipette')),
                     ('Social', (),)):
        pss = [Plugin(name=pp) for pp in ps]
        plugins.append(PluginTree(name=name, plugins=pss))
    p.plugins = plugins

    return p


def get_tree(gi, tree):
    for plugin in tree.plugins:
        if isinstance(plugin, PluginTree):
            if plugin.name.lower() == gi.lower():
                return plugin
            else:
                return get_tree(gi, plugin)


def get_plugin(name, tree):
    for plugin in tree.plugins:
        if isinstance(plugin, Plugin):
            if plugin.name.lower() == name.lower():
                return plugin


def edit_plugins():
    ip = InitializationParser()
    pev = PluginEditView(_parser=ip)
    rtree = load_tree()

    for gi in ip.get_plugin_groups():
        tree = get_tree(gi, rtree)
        if tree:
            for pp in ip.get_plugins(gi, element=True):
                plugin = get_plugin(pp.text.strip(), tree)
                if plugin:
                    plugin.enabled = to_bool(pp.get('enabled'))

    pev.plugin_tree = rtree
    info = pev.edit_traits()
    if info.result:
        pev.save()
        if confirm(None, 'Restart for changes to take effect. Restart now ?'):
            return True

# ============= EOF =============================================



