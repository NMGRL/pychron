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
from pyface.action.menu_manager import MenuManager
from pyface.confirmation_dialog import confirm
from pyface.constant import YES
from traits.api import HasTraits, Str, List, Event, Instance, Dict, Button
from traitsui.api import View, UItem, Handler, VGroup, HGroup, EnumEditor, Item
from traitsui.menu import Action
from traitsui.tree_node import TreeNode

# ============= standard library imports ========================
import os
import pickle
# ============= local library imports  ==========================
from pychron.core.ui.tree_editor import TreeEditor
from pychron.envisage.initialization.nodes import Plugin, PluginTree, PluginTreeNode, GlobalsTreeNode, GlobalTree, \
    InitializationModel, PackageTreeNode, GlobalValue, BaseNode
from pychron.envisage.initialization.utilities import DESCRIPTION_MAP, get_initialization_model, NOMINAL_DEFAULTS, \
    DEFAULTS_MAP
from pychron.paths import paths


class PEVHandler(Handler):
    def set_enabled(self, info, obj):
        info.object.set_enabled(True)

    def set_disabled(self, info, obj):
        info.object.set_enabled(False)

    def set_all_enabled(self, info, obj):
        obj.set_all_enabled(True)
        info.object.update()
        info.object.refresh_all_needed = True

    def set_all_disabled(self, info, obj):
        obj.set_all_enabled(False)
        info.object.update()
        info.object.refresh_all_needed = True


class InitializationEditView(HasTraits):
    model = Instance(InitializationModel, ())

    default = Str
    defaults = List
    defaults_map = Dict
    add_default_button = Button

    refresh_needed = Event
    refresh_all_needed = Event
    selected = List
    dclicked = Event
    description = Str
    help_str = 'Enable/Disable the active plugins.\nDouble-click to toggle or Right-click for menu options'

    def load_defaults(self):

        nominal_defaults = NOMINAL_DEFAULTS[:]
        p = os.path.join(paths.hidden_dir, 'initialization_defaults')
        if os.path.isfile(p):
            with open(p, 'r') as rfile:
                try:
                    ds = pickle.load(rfile)
                    nominal_defaults.extend(ds)
                except (pickle.PickleError, OSError, EOFError):
                    pass
        self.defaults = nominal_defaults

    def set_enabled(self, v):
        for si in self.selected:
            si.enabled = v
        self.update()

    def save(self):
        self.model.save()

    def update(self):
        self.model.update()
        self.refresh_all_needed = True

    def _set_defaults(self, new):
        if new:
            gtree, ptree = self.model.trees
            dd = DEFAULTS_MAP[new]
            dglobals = dd['globals']

            for value in gtree.values:
                name = value.name
                value.enabled = name in dglobals if dglobals else False

            for subtree in ('general', 'hardware', 'social'):
                d = dd[subtree]
                tree = ptree.get_subtree(subtree)
                for plugin in tree.plugins:
                    plugin.enabled = plugin.name in d if d else False

            self.update()

    # handlers
    def _default_changed(self, new):
        self._set_defaults(new)

    def _dclicked_fired(self):
        s = self.selected[0]
        s.enabled = not s.enabled
        self.update()

    def _selected_changed(self, new):
        desc = ''
        if new:
            node = new[0]
            name = node.name
            if isinstance(node, BaseNode) and not isinstance(node, PluginTree):
                try:
                    desc = DESCRIPTION_MAP[name]
                except KeyError:
                    pass
                desc = '{}. {}'.format(name, desc)

        self.description = desc

    def traits_view(self):
        nodes = [
            TreeNode(node_for=[InitializationModel],
                     children='trees',
                     icon_open='',
                     label='name'),
            PackageTreeNode(node_for=[PluginTree],
                            auto_open=True,
                            children='plugins',
                            label='name',
                            menu=MenuManager(Action(name='Enable All',
                                                    visible_when='not object.all_enabled',
                                                    action='set_all_enabled'),
                                             Action(name='Disable All',
                                                    visible_when='object.all_enabled',
                                                    action='set_all_disabled'))),
            PluginTreeNode(node_for=[Plugin, GlobalValue],
                           menu=MenuManager(Action(name='Enable',
                                                   action='set_enabled',
                                                   visible_when='not object.enabled'),
                                            Action(name='Disable',
                                                   visible_when='object.enabled',
                                                   action='set_disabled'), ),
                           label='name'),
            GlobalsTreeNode(node_for=[GlobalTree],
                            label='name',
                            auto_open=True,
                            children='values')]

        v = View(VGroup(HGroup(Item('default', label='Predefined Initialiation',
                                    editor=EnumEditor(name='defaults'))),
                        UItem('model', editor=TreeEditor(nodes=nodes,
                                                         editable=False,
                                                         selection_mode='extended',
                                                         selected='selected',
                                                         dclick='dclicked',
                                                         show_disabled=True,
                                                         refresh_all_icons='refresh_all_needed',
                                                         refresh_icons='refresh_needed')),
                        VGroup(UItem('description', style='readonly'), show_border=True),
                        VGroup(UItem('help_str', style='readonly'), show_border=True)),
                 title='Edit Initialization - {}'.format(self.model.path_name),
                 handler=PEVHandler(),
                 height=600,
                 width=400,
                 kind='livemodal',
                 buttons=['OK', 'Cancel'],
                 resizable=True)
        return v


def edit_initialization():
    # ip = InitializationParser()

    pev = InitializationEditView()
    pev.load_defaults()
    pev.model = get_initialization_model()

    # pev.model = model
    # pev.plugin_tree = rtree
    # do_after(1000, pev.trait_set, default='Experiment CO2')
    info = pev.edit_traits()
    if info.result:
        pev.save()
        if pev.model.is_dirty():
            return confirm(None, 'Restart for changes to take effect. Restart now?') == YES


# ============= EOF =============================================



