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

# ============= standard library imports ========================
import hashlib
# ============= enthought library imports =======================
import os
import shutil

import yaml
from traits.api import HasTraits, Str, Bool, List, Instance
from traitsui.tree_node import TreeNode

# ============= local library imports  ==========================
from pychron.core.yaml import yload
from pychron.envisage.initialization.initialization_parser import InitializationParser
from pychron.envisage.resources import icon
from pychron.paths import paths


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

    def __init__(self, factory=None, *args, **kw):
        super(Plugin, self).__init__(*args, **kw)
        if factory:
            if isinstance(factory, tuple):
                self.name, self.tests = factory
            else:
                self.name, self.tests = factory, []


class PluginTree(Plugin):
    plugins = List(Plugin)
    all_enabled = Bool
    enabled = True

    def get_subtree(self, name):
        name = name.lower()
        return next((p for p in self.plugins if isinstance(p, PluginTree) and p.name.lower() == name))

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


class StartupTesterParser:
    def __init__(self):
        self._st = self._get_st()

    def enable_plugin(self, plugin):
        for sti in self._st:
            if sti['plugin'] == plugin.name:
                sti['tests'] = plugin.tests
                break
        else:
           self._st.append({'plugin': plugin.name, 'tests': plugin.tests})

    def disable_plugin(self, plugin):
        for sti in self._st[:]:
            if sti['plugin'] == plugin.name:
                self._st.remove(sti)

    def backup(self):
        shutil.copyfile(paths.startup_tests, '{}.bk'.format(paths.startup_tests))

    def save(self):
        with open(paths.startup_tests, 'w') as wfile:
            yaml.dump(self._st, wfile)

    def _get_st(self):
        if os.path.isfile(paths.startup_tests):
            yd = yload(paths.startup_tests)
        else:
            yd = {}

        return yd


class InitializationModel(BaseNode):
    name = 'Initalization'
    trees = List  # (PluginTree)
    parser = Instance(InitializationParser)
    path_name = Str
    _hash = Str

    def init_hash(self):
        self._hash = self._current_hash()

    def _current_hash(self):
        with open(self.parser.path, 'rb') as rfile:
            return hashlib.md5(rfile.read()).hexdigest()

    def is_dirty(self):
        return self._current_hash() != self._hash

    def save(self):
        self.parser.save()

    def update(self):
        ip = self.parser
        sut = StartupTesterParser()
        sut.backup()
        for ptree in self.trees:
            if hasattr(ptree, 'plugins'):
                for pt in ptree.plugins:
                    for plugin in pt.plugins:
                        if plugin.enabled:
                            ip.enable_plugin(plugin.name, pt.name.lower(), save=False)
                            sut.enable_plugin(plugin)
                        else:
                            ip.disable_plugin(plugin.name, pt.name.lower(), save=False)
                            sut.disable_plugin(plugin)
            else:
                for vi in ptree.values:
                    ip.set_bool_tag(vi.tag, str(vi.enabled))

        sut.save()
# ============= EOF =============================================
