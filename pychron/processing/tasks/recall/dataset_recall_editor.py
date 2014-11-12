from traits.has_traits import HasTraits, on_trait_change
from traits.trait_types import Instance, List, Button, Str
from traitsui.editors import InstanceEditor, EnumEditor
from traitsui.group import HGroup, VGroup
from traitsui.item import UItem
from traitsui.view import View
from pychron.envisage.icon_button_editor import icon_button_editor

from pychron.processing.tasks.recall.recall_editor import RecallEditor


class DatasetRecallTool(HasTraits):
    selection_tool = Instance('pychron.processing.analyses.analysis_view.ViewSelection')
    prev_button = Button
    next_button = Button
    first_button = Button
    last_button = Button

    selected = Str
    available_names = List
    def traits_view(self):
        ctrl_grp = HGroup(icon_button_editor('first_button', 'arrow-left-double-2'),
                          icon_button_editor('prev_button', 'arrow-left-2'),
                          icon_button_editor('next_button', 'arrow-right-2'),
                          icon_button_editor('last_button', 'arrow-right-double-2'),
                         )
        v = View(VGroup(ctrl_grp,
                        UItem('selected', editor=EnumEditor(name='available_names')),
                        UItem('selection_tool',
                                        style='custom', editor=InstanceEditor())))
        return v


class DatasetRecallEditor(RecallEditor):
    tool = Instance(DatasetRecallTool)
    models = List
    # _parent = None
    # def create(self, parent):
    # super(DatasetRecallEditor, self).create(parent)
    #     self._parent = parent


    @on_trait_change('tool:selected')
    def _selected_changed(self, new):
        if new:
            self.set_items(next((m for m in self.models if m.record_id==new)))

    @on_trait_change('tool:[first_button, last_button]')
    def _tool_first_button_fired(self, name, new):
        idx = 0 if name == 'first_button' else -1
        self.set_items(self.models[idx])

    @on_trait_change('tool:[next_button, prev_button]')
    def _tool_next_button_fired(self, name, new):
        if name == 'next_button':
            idx = self.models.index(self.model) + 1
            if idx >= len(self.models):
                idx = 0
            self.debug('next {}'.format(idx))
        else:
            idx = self.models.index(self.model) - 1
            if idx < 0:
                idx = len(self.models) - 1
            self.debug('prev {}'.format(idx))

        self.set_items(self.models[idx])
        # self.debug('next {} {}'.format(idx, self.model))
        # self.model.analysis_view.load(self.model)
        # self.model.analysis_view.refresh_needed = True
        # self.destroy()
        # self.create(self._parent)

    #
    # @on_trait_change('tool:prev_button')
    # def _tool_prev_button_fired(self):
    #     idx = self.models.index(self.model) - 1
    #     if idx < 0:
    #         idx = len(self.models) - 1
    #
    #     self.set_items(self.models[idx])
    #     # self.model = self.models[idx]
    #     self.debug('prev {} {}'.format(idx, self.model))

    def set_items(self, item):
        super(DatasetRecallEditor, self).set_items(item)

        tool = self.model.analysis_view.selection_tool
        self.tool.selection_tool = tool

        # self.model.analysis_view.refresh_needed = True
        # self.destroy()
        # self.create(self._parent)

    # def _model_changed(self, new):
    #     tool = None
    #     if new:
    #         tool = new.analysis_view.selection_tool
    #         # self.analysis_view = new.analysis_view
    #         # print self.analysis_view
    #     self.tool.selection_tool = tool

    def _tool_default(self):
        return DatasetRecallTool()
