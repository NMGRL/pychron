from traits.has_traits import HasTraits
from traits.trait_types import Instance, List
from traitsui.item import UItem
from traitsui.view import View

from pychron.processing.tasks.recall.recall_editor import RecallEditor


class DatasetRecallTool(HasTraits):
    selection_tool = Instance('pychron.processing.analyses.analysis_view.ViewSelection')

    def traits_view(self):
        v = View(UItem('selection_tool', style='custom'))
        return v


class DatasetRecallEditor(RecallEditor):
    tool = Instance(DatasetRecallTool)
    models = List

    def _model_changed(self, new):
        tool = None
        if new:
            tool = new.analysis_view.selection_tool
        self.tool.selection_tool = tool

    def _tool_default(self):
        return DatasetRecallTool()
