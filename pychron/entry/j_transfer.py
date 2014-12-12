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
from traits.api import HasTraits, Button, Instance, Bool
from traitsui.api import View, Item, UItem, HGroup, VGroup, Controller
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.database.database_connection_spec import DBConnectionSpec
from pychron.loggable import Loggable


class TransferConfigModel(HasTraits):
    forward_transfer = Bool(True)
    conn_spec = Instance(DBConnectionSpec, ())


class TransferConfigView(Controller):
    model = Instance(TransferConfigModel)

    def traits_view(self):
        v = View(VGroup(
            VGroup(UItem('conn_spec', style='custom'),
                   show_border=True,
                   label='Connection')),
                 buttons=['OK', 'Cancel'],
                 kind='livemodal',
                 title='Configure J Transfer',
                 resizable=True)
        return v


class JTransferer(Loggable):
    pychrondb = Instance('pychron.database.adapters.isotope_adapter.IsotopeAdapter')
    massspecdb = Instance('pychron.database.adapters.massspec_database_adapter.MassSpecDatabaseAdapter')

    src = Instance('pychron.database.adapters.database_adapter.DatabaseAdapter')

    def do_transfer(self, *args):
        config = self._configure_transfer()
        if config:
            if config.forward_transfer:  # e.g. mass spec to pychron
                self._transfer_massspec_to_pychron(*args)
            else:
                self._transfer_pychron_to_massspec(*args)

    def _configure_transfer(self):
        config = TransferConfigModel()
        v = TransferConfigView(model=config)
        info = v.edit_traits()
        if info.result:
            return config

    def _transfer_massspec_to_pychron(self, *args):
        self._transfer(self._forward_transfer_func, *args)

    def _transfer_pychron_to_massspec(self, positions):
        self._transfer(self._backward_transfer_func, positions)

    def _transfer(self, func, irrad, level, positions):
        with self.massspecdb.session_ctx(), self.pychrondb.session_ctx():
            for pp in positions:
                self.debug('Transferring position {}. labnumber={} current_j={}'.format(pp.hole,
                                                                                        pp.labnumber,
                                                                                        pp.j))
                func(irrad, level, pp)

    def _forward_transfer_func(self, irrad, level, position):
        """
            transfer j from mass spec to pychron
        :param position:
        :return:
        """
        posstr = '{}{} {}'.format(irrad, level, position.hole)
        pdb = self.pychrondb
        # get the massspec irradiation_position
        ms_ip = self.massspecdb.get_irradiation_position(irrad, level, position.hole)
        if ms_ip:
            # get j for this position
            j, j_err = ms_ip.J, ms_ip.JEr
            # get the pychron irradiation_position
            pos = pdb.get_irradiation_position(irrad, level, position.hole)
            if pos.labnumber.identifier:
                def add_flux():
                    hist = pdb.add_flux_history(pos)
                    pos.labnumber.selected_flux_history = hist
                    f = pdb.add_flux(j, j_err)
                    f.history = hist

                if pos.labnumber.selected_flux_history:
                    tol = 1e-10
                    flux = pos.labnumber.selected_flux_history.flux
                    if abs(flux.j - j) > tol or abs(flux.j_err - j_err) > tol:
                        add_flux()
                    else:
                        self.info('No difference in J for {}'.format(posstr))
                else:
                    add_flux()
            else:
                self.warning('No Labnumber for {}'.format(posstr))

        else:
            self.warning('Irradiation Position {} not in MassSpecDatabase'.format(posstr))

    def _backward_transfer_func(self, irrad, level, position):
        pass

# ============= EOF =============================================



