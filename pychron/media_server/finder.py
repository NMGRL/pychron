# ===============================================================================
# Copyright 2012 Jake Ross
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

#============= enthought library imports =======================
from traits.api import HasTraits, Instance, Any
from traitsui.api import View, Item
from traitsui.tree_node import TreeNode
from traitsui.editors.tree_editor import TreeEditor
# from xml.etree.ElementTree import XMLParser
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.core.hierarchy import Hierarchy, FilePath
from pychron.regex import make_image_regex
# from pychron.core.xml.xml_parser import XMLParser

# class FilePath(HasTraits):
#     name = Str
#     root = Any
#     def make_path(self):
#         '''
#             recursively assemble the path to this resourse
#         '''
#         if self.root:
#             return '{}/{}'.format(self.root.make_path(), self.name)
#         else:
#             return self.name
#
# class Hierarchy(FilePath):
#     children = List
#
#     def _children_changed(self):
#         for ci in self.children:
#             ci.root = self


class Finder(HasTraits):
    hierarchy = Instance(Hierarchy)

    filesystem = Any
    selected = Any

    def load(self, resp, root='images', ext=None):
        resps = self.filesystem.ls(root)
        dirs, files = self._make_hierarchy(resps, root, ext)
        self.hierarchy = Hierarchy(name=root,
                                   children=dirs + files)

        for di in dirs:
            self._load_hierarchy(di, levels=1)

    def _directory_factory(self, name):
        return Hierarchy(name=name)

    def _child_factory(self, name):
        return FilePath(name=name)

    def _make_hierarchy(self, resps, name, ext=None):
        im_regex = make_image_regex(ext)
        files = filter(lambda x: im_regex.match(x), resps)
        dirs = filter(lambda x: not im_regex.match(x), resps)
        dirs = filter(lambda x: not x.startswith('.') and not x == name, dirs)
        files = [self._child_factory(ci) for ci in files]
        dirs = [self._directory_factory(di) for di in dirs]

        return dirs , files

    def _load_hierarchy(self, obj, levels=None, level=0):
        name = obj.name
        resps = self.filesystem.ls(obj.path)
        dirs, files = self._make_hierarchy(resps, name)

        obj.children = dirs + files

        if levels and level == levels:
            return

        for di in dirs:
            self._load_hierarchy(di, level=level + 1, levels=levels)

    def _on_click(self, obj, **kw):
        if isinstance(obj, Hierarchy):
            self._load_hierarchy(obj)

    def _on_select(self, obj):
        self.selected = obj.path

    def traits_view(self):

        nodes = [TreeNode(node_for=[Hierarchy],
                          children='children',
                          label='name',
                          on_click=self._on_click,
                          ),
                 TreeNode(node_for=[FilePath],
                          label='name',
                          on_select=self._on_select,
                          on_click=self._on_click,
                          )
                 ]
        v = View(Item('hierarchy',
                      show_label=False,
                      editor=TreeEditor(
                                        nodes=nodes,
                                        editable=False)),
                 resizable=True,
                 width=300,
                 height=500
                 )
        return v

if __name__ == '__main__':
    f = Finder()
    hs = [Hierarchy(name='moo{}'.format(i)) for i in range(3)]
    for j, hi in enumerate(hs):
        hi.children = [FilePath(name='foo{}{}'.format(j, i)) for i in range(5)]

    fs = [FilePath(name='foo{}'.format(i)) for i in range(10)]
    f.hierarchy = Hierarchy(name='root',
                            children=hs[:1]
#                            children=fs + hs
                            )
    f.configure_traits()
# ============= EOF =============================================
