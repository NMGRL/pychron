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



#============= enthought library imports =======================
from pyface.action.api import Action
# from pychron.envisage.core.action_helper import open_manager

#============= standard library imports ========================

#============= local library imports  ==========================

SPECTROMETER_PROTOCOL = 'pychron.spectrometer.spectrometer_manager.SpectrometerManager'
ION_OPTICS_PROTOCOL = 'pychron.spectrometer.ion_optics_manager.IonOpticsManager'
SCAN_PROTOCOL = 'pychron.spectrometer.scan_manager.ScanManager'


def get_manager(event, protocol):
    app = event.task.window.application
    manager = app.get_service(protocol)
    return manager


# class OpenIonOpticsAction(Action):
#     def perform(self, event):
#         man = get_manager(event, ION_OPTICS_PROTOCOL)
#         open_manager(event.window.application, man)

# class OpenScanManagerAction(Action):
#     accelerator = 'Ctrl+D'
#     def perform(self, event):
#         man = get_manager(event, SCAN_PROTOCOL)
#         open_manager(event.window.application, man)

# class MagFieldCalibrationAction(Action):
#    description = 'Update the magnetic field calibration table'
#    def perform(self, event):
#        app = event.window.application
#
#        manager = app.get_service(SPECTROMETER_PROTOCOL)
#        manager.peak_center(update_mftable=True)
#
class SpectrometerParametersAction(Action):
    name = 'Spectrometer Parameters...'
    description = 'View/Set spectrometer parameters'
    accelerator = 'Alt+Ctrl+S'

    def perform(self, event):
        man = get_manager(event, SPECTROMETER_PROTOCOL)
        man.open_parameters()


class PeakCenterAction(Action):
    description = 'Calculate peak center'
    name = 'Peak Center...'

    def perform(self, event):
        man = get_manager(event, ION_OPTICS_PROTOCOL)
        if man.setup_peak_center():
            man.do_peak_center(confirm_save=True, warn=True)


class CoincidenceScanAction(Action):
    name = 'Coincidence...'

    def perform(self, event):
        man = get_manager(event, SPECTROMETER_PROTOCOL)
        man.coincidence_scan_task_factory()


class RelativePositionsAction(Action):
    def perform(self, event):
        man = get_manager(event, SPECTROMETER_PROTOCOL)


class CDDOperateVoltageAction(Action):
    def perform(self, event):
        man = get_manager(event, SPECTROMETER_PROTOCOL)
        man.cdd_operate_voltage_scan_task_factory()


class MagnetFieldTableAction(Action):
    name = 'Edit MF Table...'

    def perform(self, event):
        man = get_manager(event, SPECTROMETER_PROTOCOL)
        if man.spectrometer:
            mft = man.spectrometer.magnet.mftable

            from pychron.spectrometer.mftable import MagnetFieldTableView

            mv = MagnetFieldTableView(model=mft)
            mv.edit_traits()


class MagnetFieldTableHistoryAction(Action):
    name = 'Local MFTable History...'

    def perform(self, event):
        man = get_manager(event, SPECTROMETER_PROTOCOL)
        if man.spectrometer:
            from pychron.git_archive.history import GitArchiveHistory, GitArchiveHistoryView
            import os

            mft = man.spectrometer.magnet.mftable
            archive_root = mft.mftable_archive_path
            if os.path.isfile(os.path.join(archive_root, os.path.basename(mft.mftable_path))):
                gh = GitArchiveHistory(archive_root, mft.mftable_path)
                gh.load_history(os.path.basename(mft.mftable_path))
                ghv = GitArchiveHistoryView(model=gh, title='MFTable Archive')
                ghv.edit_traits(kind='livemodal')
            else:
                man.warning_dialog('No MFTable History')


class DBMagnetFieldTableHistoryAction(Action):
    name = 'DB MFTable History...'

    def perform(self, event):
        man = get_manager(event, SPECTROMETER_PROTOCOL)
        if man.spectrometer:
            from pychron.spectrometer.mftable_history_view import MFTableHistory, MFTableHistoryView

            mft = man.spectrometer.magnet.mftable
            mfh = MFTableHistory(checkout_path=mft.mftable_path,
                                 spectrometer=man.spectrometer.name)
            mfh.load_history()
            mv = MFTableHistoryView(model=mfh)
            mv.edit_traits()

#============= EOF ====================================
