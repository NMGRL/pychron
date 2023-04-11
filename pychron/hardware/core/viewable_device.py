# ===============================================================================
# Copyright 2011 Jake Ross
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
# =============enthought library imports=======================
from datetime import datetime
from traits.api import Str, Property, Bool, CStr, Button, HasTraits, Event
from traitsui.api import View, Item, Group, VGroup, TextEditor, UItem, Tabbed

# =============standard library imports ========================

# =============local library imports  ==========================


class ViewableDevice(HasTraits):
    """ """

    simulation = Property

    connected = Property(depends_on="simulation")
    com_class = Property

    loaded = Property(depends_on="_loaded")
    _loaded = Bool

    klass = Property
    config_short_path = Property

    last_command = Str
    last_response = CStr
    _last_timestamp = None
    timestamp = None
    # response_updated = Event
    # auto_handle_response = Bool(True)

    current_scan_value = CStr

    reinitialize_button = Button("Reinitialize")

    display_address = Property

    communicator = None

    def __init__(self, *args, **kw):
        super(ViewableDevice, self).__init__(*args, **kw)
        self.doc = self._build_doc()

    def _build_doc(self):
        return self.__class__.__doc__

    def get_control_group(self):
        pass

    def get_configure_group(self):
        pass

    def current_state_view(self):
        gen_grp = Group(
            Item("last_command", style="readonly"),
            Item("last_response", style="readonly"),
            Item("current_scan_value", style="readonly"),
            label="General",
        )
        doc_grp = Group(
            UItem("doc", style="custom", editor=TextEditor(read_only=True)), label="Doc"
        )

        tabs = (gen_grp, doc_grp)
        atabs = self.get_additional_tabs()
        if atabs:
            tabs += atabs

        v = View(Tabbed(*tabs))

        return v

    def get_additional_tabs(self):
        return

    def info_view(self):
        info_grp = VGroup(
            Item("reinitialize_button", show_label=False),
            Item("name", style="readonly"),
            Item("display_address", style="readonly"),
            Item("klass", style="readonly", label="Class"),
            Item("connected", style="readonly"),
            Item("com_class", style="readonly", label="Com. Class"),
            Item("config_short_path", style="readonly"),
            Item("loaded", style="readonly"),
            label="Info",
        )

        grp = Group(layout="tabbed")
        cg = self.get_control_group()
        if cg:
            cg.label = "Control"
            grp.content.append(cg)

        config_group = self.get_configure_group()
        if config_group:
            config_group.label = "Configure"
            grp.content.append(config_group)

        grp.content.append(info_grp)
        v = View(grp)

        return v

    # def setup_response_readback(self, func):
    #     self.on_trait_change(func, 'response_updated')

    def traits_view(self):
        v = View()
        cg = self.get_control_group()
        if cg:
            v.content.content.append(cg)
        return v

    def _reinitialize(self):
        self.bootstrap()

    def _reinitialize_button_fired(self):
        self._reinitialize()

    def _get_display_address(self):
        if hasattr(self.communicator, "host"):
            return self.communicator.host
        elif hasattr(self, "port"):
            return self.port
        elif hasattr(self.communicator, "port"):
            return self.communicator.port

        return ""

    def _get_config_short_path(self):
        """
        config_path is an attribute of
        """
        items = self.config_path.split("/")
        return "/".join(items[6:])

    def _get_loaded(self):
        return "Yes" if self._loaded else "No"

    def _get_klass(self):
        return self.__class__.__name__

    def _get_com_class(self):
        if self.communicator:
            return self.communicator.__class__.__name__

    def _get_connected(self):
        return "Yes" if not self._get_simulation() else "No"

    def _get_simulation(self):
        if self.communicator is not None:
            return self.communicator.simulation
        else:
            return True

    def _communicate_hook(self, cmd, r):
        if isinstance(cmd, bytes):
            cmd = "".join(("[{}]".format(str(b)) for b in cmd))

        now = datetime.now()
        fmt = "%H:%M:%S"
        if self._last_timestamp:
            if now.day != self._last_timestamp.day:
                fmt = "%m/%d %H:%M:%S"

        self.timestamp = now.strftime(fmt)
        self._last_timestamp = now

        # print(self, cmd, r)
        self.last_command = str(cmd)
        self.last_response = str(r) if r else ""
        # if self.auto_handle_response:
        #     self.response_updated = {'value': self.last_response, 'command': self.last_command}


# ============= EOF =====================================
