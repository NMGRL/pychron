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

from apptools.preferences.preference_binding import bind_preference

from pychron.envisage.view_util import open_view
from pychron.spectrometer.base_spectrometer_manager import BaseSpectrometerManager
from pychron.spectrometer.jobs.cdd_operating_voltage_scan import CDDOperatingVoltageScan
from pychron.spectrometer.jobs.relative_detector_positions import RelativeDetectorPositions
from pychron.spectrometer.spectrometer_parameters import SpectrometerParameters, \
    SpectrometerParametersView


class ThermoSpectrometerManager(BaseSpectrometerManager):
    """
    Top level interface to an Thermo Scientific Argus Mass Spectrometer

    direct access provided by spectrometer_microcontroller; an instance
    of thermo.spectrometer.Spectrometer

    """

    def protect_detector(self, det, protect):
        protect = 'On' if protect else 'Off'
        self.spectrometer.set_parameter('ProtectDetector', '{},{}'.format(det, protect))

    def set_deflection(self, det, defl):
        self.spectrometer.set_deflection(det, defl)

    def open_parameters(self):
        p = SpectrometerParameters(spectrometer=self.spectrometer)
        p.load()

        v = SpectrometerParametersView(model=p)
        v.edit_traits()

    def make_gains_dict(self):
        spec = self.spectrometer
        return {di.name: di.get_gain() for di in spec.detectors}

    def set_gains(self, *args, **kw):
        spec = self.spectrometer

        diff = any([di.gain_outdated for di in spec.detectors])
        if diff:
            return spec.set_gains(*args, **kw)

    def make_parameters_dict(self):
        spec = self.spectrometer
        d = dict()
        for attr, cmd in [('extraction_lens', 'ExtractionLens'),
                          ('ysymmetry', 'YSymmetry'),
                          ('zsymmetry', 'ZSymmetry'),
                          ('zfocus', 'ZFocus')]:
            v = spec.get_parameter('Get{}'.format(cmd))
            if v is not None:
                d[attr] = v

        return d

    def make_deflections_dict(self):
        spec = self.spectrometer
        d = dict()
        for di in spec.detectors:
            d[di.name] = di.read_deflection()
        return d

    def bind_preferences(self):
        pref_id = 'pychron.spectrometer'
        bind_preference(self.spectrometer, 'send_config_on_startup',
                        '{}.send_config_on_startup'.format(pref_id))

        bind_preference(self.spectrometer.magnet, 'confirmation_threshold_mass',
                        '{}.confirmation_threshold_mass'.format(pref_id))

    def relative_detector_positions_task_factory(self):
        return self._factory(RelativeDetectorPositions)

        # def do_coincidence_scan(self):
        #     obj = self._factory(CoincidenceScan)
        #     obj.inform = False
        #     self.open_view(obj.graph)
        #     t = obj.execute()
        #     return obj, t
        # def coincidence_scan_task_factory(self):
        # obj = self._factory(CoincidenceScan)
        # info = obj.edit_traits(view='edit_view',
        #                        kind='livemodal')
        # if info.result:
        #     self.open_view(obj.graph)
        #     obj.execute()

    def cdd_operate_voltage_scan_task_factory(self):
        obj = CDDOperatingVoltageScan(spectrometer=self.spectrometer)
        info = obj.edit_traits(kind='livemodal')
        if info.result:
            open_view(obj.graph)
            obj.execute()

    def _factory(self, klass):
        ion = self.application.get_service('pychron.spectrometer.ion_optics_manager.IonOpticsManager')
        return klass(spectrometer=self.spectrometer, ion_optics_manager=ion)




# ============= EOF =============================================



