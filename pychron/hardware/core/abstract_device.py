#===============================================================================
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
#===============================================================================

#=============enthought library imports=======================
from traits.api import Property, DelegatesTo, Instance, implements
#=============standard library imports ========================
#=============local library imports  ==========================
# from pychron.config_loadable import ConfigLoadable
# from traits.has_traits import provides
from pychron.hardware.core.i_core_device import ICoreDevice
# from viewable_device import ViewableDevice
from pychron.has_communicator import HasCommunicator
from pychron.rpc.rpcable import RPCable
from pychron.hardware.core.core_device import CoreDevice
# from pychron.hardware.core.viewable_device import ViewableDevice
from pychron.hardware.core.scanable_device import ScanableDevice

# @provides(ICoreDevice)
class AbstractDevice(ScanableDevice, RPCable, HasCommunicator):
#class AbstractDevice(RPCable, HasCommunicator):
    """
    """
    implements(ICoreDevice)
    _cdevice = Instance(CoreDevice)
    _communicator = DelegatesTo('_cdevice')

    dev_klass = Property(depends_on='_cdevice')
    #     simulation = Property(depends_on='_cdevice')
    #    reinitialize_button = DelegatesTo('_cdevice')
    #    com_class = Property(depends_on='_cdevice')

    #    last_command = Property(depends_on='_cdevice.last_command')
    #    last_response = Property(depends_on='_cdevice.last_response')
    #
    #    scan_units = DelegatesTo('_cdevice')
    #    scan_func = DelegatesTo('_cdevice')
    #    scan_period = DelegatesTo('_cdevice')
    #    scan_button = DelegatesTo('_cdevice')
    #    scan_label = DelegatesTo('_cdevice')
    #    _scanning = DelegatesTo('_cdevice')
    #    scan_path = DelegatesTo('_cdevice')
    #    last_command = DelegatesTo('_cdevice')
    #    last_response = DelegatesTo('_cdevice')
    # #    simulation = DelegatesTo('_cdevice')
    #    com_class = DelegatesTo('_cdevice')
    #    is_scanable = DelegatesTo('_cdevice')
    #    dm_kind = DelegatesTo('_cdevice')
    graph = DelegatesTo('_cdevice')
    #    graph_ytitle=DelegatesTo('_cdevice')

    def __getattr__(self, attr):
        #print 'abstrcat {}'.format(attr)
        if hasattr(self._cdevice, attr):
            return getattr(self._cdevice, attr)
            #try:
            #except AttributeError, e:
            #    self.debug(e)

    def _get_dev_klass(self):
        return self._cdevice.__class__.__name__

    def get_factory(self, package, klass):
        try:
            module = __import__(package, fromlist=[klass])
            if hasattr(module, klass):
                factory = getattr(module, klass)
                return factory
        except ImportError, e:
            self.warning(e)

    def post_initialize(self, *args, **kw):
        self.graph.set_y_title(self.graph_ytitle)


        #use our scan configuration not the cdevice's
        self.setup_scan()
        self.setup_alarms()
        self.setup_scheduler()

        if self.auto_start:
            self.start_scan()


    def load(self, *args, **kw):
        config = self.get_configuration()
        if config:

            if self.load_additional_args(config):
                self._loaded = True
                self._cdevice.load()
                return True

                #def current_state_view(self):
                #    g = VGroup(Item('graph', show_label=False, style='custom'),
                #               VGroup(Item('scan_func', label='Function', style='readonly'),
                #
                #                      HGroup(Item('scan_period', label='Period ({})'.format(self.scan_units),
                #                                  # style='readonly'
                #                      ), spring),
                #                      Item('current_scan_value', style='readonly'),
                #               ),
                #
                #               VGroup(
                #                   HGroup(Item('scan_button',
                #                               editor=ButtonEditor(label_value='scan_label'),
                #                               show_label=False),
                #                          spring
                #                   ),
                #                   Item('scan_root',
                #                        style='readonly',
                #                        label='Scan directory',
                #                        visible_when='record_scan_data'),
                #                   Item('scan_name', label='Scan name',
                #                        style='readonly',
                #                        visible_when='record_scan_data'),
                #                   visible_when='is_scanable'),
                #
                #               label='Scan'
                #    )
                #    #return View(g)
                #    v = super(AbstractDevice, self).current_state_view()
                #    v.content.content.append(g)
                #    return v

#===============================================================================
# viewable device protocol
#===============================================================================
#    def _get_last_command(self):
#        return self._cdevice.last_command
#    def _get_last_response(self):
#        return self._cdevice.last_response

#    def _get_com_class(self):
#        if self._cdevice is not None:
#            return self._cdevice.com_class
#
#     def _get_simulation(self):
#         '''
#         '''
#         r = True
#         if self._cdevice is not None:
#             r = self._cdevice.simulation
#         return r

#    def info_view(self):
#        v = View()
#        return v
#    def traits_view(self):
#        v = View(Item('name', style='readonly'),
#                 Item('klass', style='readonly', label='Class'),
#                 Item('dev_klass', style='readonly', label='Dev. Class'),
#                 Item('connected', style='readonly'),
#                 Item('com_class', style='readonly', label='Com. Class'),
#                 Item('config_short_path', style='readonly'),
#                 Item('loaded', style='readonly'),
#
#               )
#        return v
#============= EOF =====================================
