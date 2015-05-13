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
from traitsui.tree_node import TreeNode
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.resources import icon


class _TreeNode(TreeNode):
    icon_name = ''
    label = 'name'

    def get_icon(self, object, is_expanded):
        name = self.icon_name
        if not object.enabled:
            name = 'cancel'

        return icon(name)


class DataTreeNode(_TreeNode):
    icon_name = 'table'


class FilterTreeNode(_TreeNode):
    icon_name = 'filter'


class IdeogramTreeNode(_TreeNode):
    icon_name = 'histogram'


class SpectrumTreeNode(_TreeNode):
    icon_name = ''


class SeriesTreeNode(_TreeNode):
    icon_name = ''


class PDFTreeNode(_TreeNode):
    icon_name = 'file_pdf'


class GroupingTreeNode(_TreeNode):
    pass

# ============= EOF =============================================



