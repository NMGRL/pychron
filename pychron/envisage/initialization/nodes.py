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
import hashlib

from traits.api import HasTraits, Str, Bool, List, Instance

# ============= standard library imports ========================
#============= local library imports  ==========================
from traitsui.tree_node import TreeNode
from pychron.envisage.initialization.initialization_parser import InitializationParser
from pychron.envisage.resources import icon


class GlobalsTreeNode(TreeNode):
    def get_icon(self, object, is_expanded):
        return icon('cog')


class PluginTreeNode(TreeNode):
    def get_icon(self, obj, is_expanded):
        if obj.enabled:
            return icon('tick')
        else:
            return icon('cancel')


class PackageTreeNode(TreeNode):
    def get_icon(self, object, is_expanded):
        return icon('package-green')


class BaseNode(HasTraits):
    name = Str
    enabled = Bool


class Plugin(BaseNode):
    pass


class PluginTree(Plugin):
    plugins = List(Plugin)
    all_enabled = Bool
    enabled = True

    def set_all_enabled(self, v):
        """

        :param v: bool true=enabled false=disabled
        :return:
        """
        for pi in self.plugins:
            if isinstance(pi, PluginTree):
                pi.set_all_enabled(v)
            pi.enabled = v
        self.all_enabled = v


class GlobalValue(BaseNode):
    pass


class GlobalTree(BaseNode):
    name = 'Globals'
    values = List(GlobalValue)

    def get_value(self, tag):
        return next((ni for ni in self.values if ni.tag == tag), None)


class InitializationModel(BaseNode):
    name = 'Initalization'
    trees = List  #(PluginTree)
    parser = Instance(InitializationParser)
    path_name = Str
    _hash = Str


    def init_hash(self):
        self._hash = self._current_hash()

    def _current_hash(self):
        with open(self.parser.path) as fp:
            return hashlib.md5(fp.read()).hexdigest()

    def is_dirty(self):
        return self._current_hash()!=self._hash

    def save(self):
        self.parser.save()

    def update(self):
        ip = self.parser
        for ptree in self.trees:
            if hasattr(ptree, 'plugins'):
                for pt in ptree.plugins:
                    for plugin in pt.plugins:
                        if plugin.enabled:
                            ip.enable_plugin(plugin.name, pt.name.lower(), save=False)
                        else:
                            ip.disable_plugin(plugin.name, save=False)
            else:
                for vi in ptree.values:
                    ip.set_bool_tag(vi.tag, str(vi.enabled))


#============= EOF =============================================



