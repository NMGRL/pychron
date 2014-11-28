# ===============================================================================
# Copyright 2011 Jake Ross
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
from traits.api import List, Any
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.managers.manager import Manager
# from pychron.hardware.core.i_core_device import ICoreDevice
class HardwareManager(Manager):
    devices = List
    #    application = Any
    selected = Any
    current_device = Any
    #    current_device = Instance(ICoreDevice)

    #    @on_trait_change('application')
    #    def app_changed(self, obj, name, old, new):
    #        if name == 'application' and new:
    #            self.load_devices()
    #            self.application = new

    def _application_changed(self):
        self.load_devices()

    def load_devices(self):
        self.devices = self.application.service_registry.get_services('pychron.hardware.core.i_core_device.ICoreDevice',
                                                                      "display==True")
        self.devices.sort()

    def _selected_changed(self):
        if self.selected is not None:
            self.current_device = self.selected

#    def current_device_view(self):
#        return View(Item('current_device',
#                         editor=InstanceEditor(view='current_state_view'),
#                         style='custom',
#                         show_label=False
#                         ))
#    def traits_view(self):
#        cols = [ObjectColumn(name='name'),
#                ObjectColumn(name='connected'),
#                ObjectColumn(name='com_class', label='Com. Class'),
#                ObjectColumn(name='klass', label='Class'),
#
#                ]
#        table_editor = TableEditor(columns=cols,
#                                   editable=False,
#                                   selected='selected',
#                                   selection_mode='row'
#
#                                   )
#        v = View(
#                 VSplit(
#                     Item('devices', editor=table_editor,
#                          show_label=False,
#
#                          height=0.45,
#                          ),
#
#                     Item('current_device', show_label=False,
#                          style='custom',
#                          editor=InstanceEditor(view='info_view'),
#                          height=0.75,
#                          width=0.5
#                          ),
#                      ),
#                width=650,
#                height=500,
#                 resizable=True)
#
#
#        return v

if __name__ == '__main__':
    hw = HardwareManager()
    hw.configure_traits()


# ============= EOF =============================================
