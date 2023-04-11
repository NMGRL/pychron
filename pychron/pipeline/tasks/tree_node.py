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
from __future__ import absolute_import
from pyface.qt.QtCore import Qt
from pyface.qt.QtGui import QColor
from traitsui.tree_node import TreeNode

from pychron.envisage.resources import icon
from pychron.pipeline.engine import Pipeline
from pychron.pipeline.nodes import ReviewNode


class PipelineGroupTreeNode(TreeNode):
    icon_name = ""
    label = "name"


ICON_MAP = {}


class PipelineTreeNode(TreeNode):
    icon_name = ""
    label = "name"

    def get_background(self, obj):
        if isinstance(obj, Pipeline):
            c = QColor(Qt.white)
        else:
            if isinstance(obj, ReviewNode):
                if not obj.enabled:
                    c = QColor("#ff8080")  # light red
                else:
                    c = QColor(Qt.cyan)
            elif obj.skip_configure:
                c = QColor("#D05BFF")
            elif not obj.enabled:
                c = QColor("#ff8080")  # light red
            else:
                c = super(PipelineTreeNode, self).get_background(obj)
        return c

    def get_status_color(self, obj):
        c = QColor(Qt.white)
        if not isinstance(obj, Pipeline):
            c = QColor(Qt.lightGray)
            if not obj.enabled:
                c = QColor("lightblue")
            elif obj.visited:
                c = QColor("#0dbf81")
            elif obj.active:
                c = QColor("orange")
        return c

    def get_icon(self, obj, is_expanded):
        name = self.icon_name
        if not isinstance(obj, Pipeline):
            if not obj.enabled:
                name = "cancel"

        if name in ICON_MAP:
            i = ICON_MAP[name]
        else:
            if not name:
                name = "large_tiles"
            i = icon(name)
            ICON_MAP[name] = i

        return i

        # def get_background(self, obj):
        #     # print 'get', obj, obj.visited
        #     return 'green' if obj.visited else 'white'


class NodeGroupTreeNode(PipelineTreeNode):
    icon_name = ""


class DataTreeNode(PipelineTreeNode):
    icon_name = "table"


class FilterTreeNode(PipelineTreeNode):
    icon_name = "table_filter"


class IdeogramTreeNode(PipelineTreeNode):
    icon_name = "histogram"


class SpectrumTreeNode(PipelineTreeNode):
    icon_name = ""


class SeriesTreeNode(PipelineTreeNode):
    icon_name = ""


class PDFTreeNode(PipelineTreeNode):
    icon_name = "file_pdf"


class GroupingTreeNode(PipelineTreeNode):
    pass


class DBSaveTreeNode(PipelineTreeNode):
    icon_name = "database_save"


class FindTreeNode(PipelineTreeNode):
    icon_name = "find"


class FitTreeNode(PipelineTreeNode):
    icon_name = "lightning"


class ReviewTreeNode(PipelineTreeNode):
    pass


# ============= EOF =============================================
