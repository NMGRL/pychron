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


# ============= enthought library imports =======================
from traits.api import Property
from pyface.action.api import Action
from pyface.timer.do_later import do_later
from pyface.tasks.action.task_action import TaskAction
# ============= standard library imports ========================

# ============= local library imports  ==========================
from pychron.envisage.tasks.actions import myTaskAction
from pychron.paths import paths

from pychron.pychron_constants import SPECTROMETER_PROTOCOL, SCAN_PROTOCOL, EL_PROTOCOL, ION_OPTICS_PROTOCOL


def get_manager(event, protocol):
    app = event.task.window.application
    manager = app.get_service(protocol)
    return manager


# class OpenIonOpticsAction(Action):
# def perform(self, event):
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

class AutoMFTableAction(Action):
    name = 'Auto MFTable'

    def perform(self, event):
        app = event.task.window.application

        kw = {}
        for attr, prot, msg in (('spectrometer_manager', SPECTROMETER_PROTOCOL, 'Spectrometer Manager'),
                                ('ion_optics_manager', ION_OPTICS_PROTOCOL, 'Ion Optics Manager'),
                                ('el_manager', EL_PROTOCOL, 'Extraction Line Manager')):
            srv = app.get_service(prot)
            if not srv:
                app.warning('No {} available'.format(msg))
                return
            kw[attr] = srv

        pyscript_task = app.get_task('pychron.pyscript.task', activate=False)
        if not pyscript_task:
            app.warning('PyScript Plugin not available')

        from pychron.spectrometer.auto_mftable import AutoMFTable

        a = AutoMFTable(pyscript_task=pyscript_task, **kw)

        do_later(a.do_auto_mftable)


class SendConfigAction(myTaskAction):
    name = 'Send Configuration'
    method = 'send_configuration'
    task_ids = ['pychron.spectrometer']


class EditGainsAction(Action):
    name = 'Edit Gains...'

    def perform(self, event):
        from pychron.spectrometer.gains_edit_view import GainsModel, GainsEditView

        app = event.task.window.application
        spec = app.get_service(SPECTROMETER_PROTOCOL)
        gv = GainsModel(spectrometer=spec.spectrometer)

        man = app.get_service('pychron.database.isotope_database_manager.IsotopeDatabaseManager')
        if man:
            gv.db = man.db

        gv.load_histories()
        spec.spectrometer.load_current_detector_gains()

        gev = GainsEditView(model=gv)
        gev.edit_traits(kind='livemodal')


class ToggleSpectrometerTask(TaskAction):
    name = Property(depends_on='task')

    def _get_name(self):
        if self.task:
            return 'Switch to Scan' if self.task.id == 'pychron.spectrometer.scan_inspector' \
                else 'Switch to Inspector'
        else:
            return ''

    def perform(self, event):
        window = event.task.window
        if event.task.id == 'pychron.spectrometer':
            tid = 'pychron.spectrometer.scan_inspector'
        else:
            tid = 'pychron.spectrometer'

        task = window.application.create_task(tid)
        window.add_task(task)
        window.activate_task(task)


class SpectrometerParametersAction(Action):
    name = 'Spectrometer Parameters...'
    description = 'View/Set spectrometer parameters'
    accelerator = 'Alt+Ctrl+S'

    def perform(self, event):
        man = get_manager(event, SPECTROMETER_PROTOCOL)
        man.open_parameters()


class PeakCenterAction(TaskAction):
    description = 'Calculate peak center'
    name = 'Peak Center...'

    def perform(self, event):
        man = get_manager(event, SCAN_PROTOCOL)
        man.peak_center()

        # if man.setup_peak_center(new=True):
        #     man.do_peak_center(confirm_save=True, warn=True, message='manual peakcenter')


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
            import os

            mft = man.spectrometer.magnet.mftable
            archive_root = mft.mftable_archive_path
            if os.path.isfile(os.path.join(archive_root, os.path.basename(paths.mftable))):
                # from pychron.git_archive.history import GitArchiveHistory, GitArchiveHistoryView
                from pychron.spectrometer.local_mftable_history_view import LocalMFTableHistory, LocalMFTableHistoryView

                gh = LocalMFTableHistory(paths.mftable, archive_root)
                gh.load_history(paths.mftable)
                # gh.load_history(os.path.basename(mft.mftable_path))
                ghv = LocalMFTableHistoryView(model=gh, title='MFTable Archive')
                ghv.edit_traits(kind='livemodal')
            else:
                man.warning_dialog('No MFTable History')


class DBMagnetFieldTableHistoryAction(Action):
    name = 'DB MFTable History...'

    def perform(self, event):
        man = get_manager(event, SPECTROMETER_PROTOCOL)
        if man.spectrometer:
            from pychron.spectrometer.mftable_history_view import MFTableHistory, MFTableHistoryView

            mfh = MFTableHistory(checkout_path=paths.mftable,
                                 spectrometer=man.spectrometer.name)
            mfh.load_history()
            mv = MFTableHistoryView(model=mfh)
            mv.edit_traits()

# ============= EOF ====================================
