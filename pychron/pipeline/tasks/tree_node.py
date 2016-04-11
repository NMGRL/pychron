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
from PySide.QtCore import Qt
from PySide.QtGui import QColor
from traitsui.tree_node import TreeNode
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.resources import icon
#
# class PipelineTreeNode(TreeNode):
#     def get_status_color(self, obj):
#         c = QColor('black')
#         if obj.status == 'ran':
#             c = QColor('green')
#         elif obj.status == 'paused':
#             c = QColor('orange')
#         return c
from pychron.pipeline.nodes import ReviewNode


class PipelineTreeNode(TreeNode):
    icon_name = ''
    label = 'name'

    def get_background(self, obj):
        if isinstance(obj, ReviewNode):
            c = QColor(Qt.cyan)
        elif obj.skip_configure:
            c = QColor('#D05BFF')
        else:
            c = super(PipelineTreeNode, self).get_background(obj)
        return c

    def get_status_color(self, obj):
        c = QColor(Qt.lightGray)

        if obj.visited:
            c = QColor(Qt.green)
        elif obj.active:
            c = QColor('orange')
        # if obj.status == 'ran':
        #     c = QColor('green')
        # elif obj.status == 'paused':
        #     c = QColor('orange')
        return c

    def get_icon(self, object, is_expanded):
        name = self.icon_name
        if not object.enabled:
            name = 'cancel'

        return icon(name)

        # def get_background(self, obj):
        #     # print 'get', obj, obj.visited
        #     return 'green' if obj.visited else 'white'


class DataTreeNode(PipelineTreeNode):
    icon_name = 'table'


class FilterTreeNode(PipelineTreeNode):
    icon_name = 'table_filter'


class IdeogramTreeNode(PipelineTreeNode):
    icon_name = 'histogram'


class SpectrumTreeNode(PipelineTreeNode):
    icon_name = ''


class SeriesTreeNode(PipelineTreeNode):
    icon_name = ''


class PDFTreeNode(PipelineTreeNode):
    icon_name = 'file_pdf'


class GroupingTreeNode(PipelineTreeNode):
    pass


class DBSaveTreeNode(PipelineTreeNode):
    icon_name = 'database_save'


class FindTreeNode(PipelineTreeNode):
    icon_name = 'find'


class FitTreeNode(PipelineTreeNode):
    icon_name = 'lightning'

# ============= EOF =============================================
