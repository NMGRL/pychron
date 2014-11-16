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
from PySide.QtGui import QTreeWidgetItem, QIcon
from traits.api import HasTraits, Button, Str, Int, Bool, Event
from traitsui.api import View, Item, UItem, HGroup, VGroup, TreeEditor as _TreeEditor
# ============= standard library imports ========================
#============= local library imports  ==========================


from traitsui.qt4.tree_editor import SimpleEditor as _SimpleEditor


class SimpleEditor(_SimpleEditor):
    refresh_icons = Event
    refresh_all_icons = Event

    def _refresh_all_icons_fired(self):
        ctrl = self.control
        item = ctrl.currentItem()
        self._refresh_icons(item)
        self._refresh_icons(item.parent())

    def _refresh_icons(self, tree):
        """
            recursively refresh the nodes
        """
        for i in range(tree.childCount()):
            node = tree.child(i)
            self._update_icon(node)
            self._refresh_icons(node)

    def _refresh_icons_fired(self):
        ctrl = self.control
        item = ctrl.currentItem()
        self._update_icon(item)

    def init(self, parent):
        super(SimpleEditor, self).init(parent)
        self.sync_value(self.factory.refresh_icons, 'refresh_icons', 'from')
        self.sync_value(self.factory.refresh_all_icons, 'refresh_all_icons', 'from')


    def _get_icon( self, node, obj, is_expanded = False ):
        if not self.factory.show_disabled and not obj.enabled:
            return QIcon()
        return super(SimpleEditor, self)._get_icon(node, obj, is_expanded)

class TreeEditor(_TreeEditor):
    refresh_icons = Str
    refresh_all_icons = Str
    show_disabled = Bool
    def _get_simple_editor_class(self):
        """
        """
        return SimpleEditor

#============= EOF =============================================



