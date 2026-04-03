from traits.api import Any, HasTraits, Instance, Property
from traitsui.api import Item, View, VGroup

from pychron.extraction_line.canvas.state import CanvasSystemState


class ExtractionLineCanvasViewModel(HasTraits):
    state = Instance(CanvasSystemState, ())
    active_item = Any
    selected_item = Any
    selected_name = Property(depends_on="selected_item")
    selected_description = Property(depends_on="selected_item")
    selected_owner = Property(depends_on="selected_item")
    selected_address = Property(depends_on="selected_item")
    selected_last_state = Property(depends_on="selected_item")
    selected_last_readback = Property(depends_on="selected_item")
    selected_blocked_reason = Property(depends_on="selected_item")
    selected_connected_volume = Property(depends_on="selected_item")

    def set_state(self, state):
        self.state = state
        if state is None:
            self.active_item = None
            self.selected_item = None
            return

        self.active_item = state.get_valve(state.active_item)
        self.selected_item = state.get_valve(state.selected_item)

    def set_active_item(self, name):
        self.active_item = self.state.get_valve(name) if self.state else None

    def set_selected_item(self, name):
        self.selected_item = self.state.get_valve(name) if self.state else None

    def _get_selected_name(self):
        return getattr(self.selected_item, "name", "")

    def _get_selected_description(self):
        return getattr(self.selected_item, "description", "")

    def _get_selected_owner(self):
        return getattr(self.selected_item, "owner", "")

    def _get_selected_address(self):
        return getattr(self.selected_item, "address", "")

    def _get_selected_last_state(self):
        return getattr(self.selected_item, "last_state_timestamp", "")

    def _get_selected_last_readback(self):
        return getattr(self.selected_item, "last_readback_timestamp", "")

    def _get_selected_blocked_reason(self):
        return getattr(self.selected_item, "cannot_actuate_reason", "")

    def _get_selected_connected_volume(self):
        return getattr(self.selected_item, "connected_volume", 0)

    def traits_view(self):
        return View(
            VGroup(
                Item("selected_name", label="Name", style="readonly"),
                Item("selected_description", label="Description", style="readonly"),
                Item("selected_owner", label="Owner", style="readonly"),
                Item("selected_address", label="Address", style="readonly"),
                Item("selected_last_state", label="Last State", style="readonly"),
                Item("selected_last_readback", label="Last Readback", style="readonly"),
                Item("selected_blocked_reason", label="Blocked", style="readonly"),
                Item("selected_connected_volume", label="Volume", style="readonly"),
            )
        )
