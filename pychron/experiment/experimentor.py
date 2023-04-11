# ===============================================================================
# Copyright 2013 Jake Ross
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
from __future__ import absolute_import

from traits.api import Instance, List, on_trait_change, Bool, Event

from pychron.dvc.dvc_irradiationable import DVCIrradiationable
from pychron.experiment.experiment_executor import ExperimentExecutor
from pychron.experiment.factory import ExperimentFactory
from pychron.experiment.queue.experiment_queue import ExperimentQueue


class Experimentor(DVCIrradiationable):
    experiment_factory = Instance(ExperimentFactory)
    experiment_queue = Instance(ExperimentQueue)
    executor = Instance(ExperimentExecutor)
    experiment_queues = List
    # stats = Instance(StatsGroup, ())

    mode = None
    # unique_executor_db = False

    save_enabled = Bool

    # ===========================================================================
    # permissions
    # ===========================================================================
    # max_allowable_runs = 10000
    #    can_edit_scripts = True
    #    _last_ver_time = None
    #    _ver_timeout = 10

    # ===========================================================================
    # task events
    # ===========================================================================

    activate_editor_event = Event
    save_event = Event

    def prepare_destory(self):
        if self.executor:
            if self.executor.datahub:
                self.executor.datahub.prepare_destroy()
        if self.experiment_factory:
            if self.experiment_factory.run_factory:
                if self.experiment_factory.run_factory.datahub:
                    self.experiment_factory.run_factory.datahub.prepare_destroy()

    def load(self):
        self.experiment_factory.queue_factory.db_refresh_needed = True
        self.experiment_factory.run_factory.db_refresh_needed = True

        return True

    def reset_run_generator(self):
        if self.executor.is_alive():
            self.debug("Queue modified. Reset run generator")
            #             self.executor.queue_modified = True
            self.executor.set_queue_modified()

    def refresh_executable(self, qs=None):
        if qs is None:
            qs = self.experiment_queues

        if self.executor.is_alive():
            qs = (self.executor.experiment_queue,)

        self.executor.executable = all([ei.is_executable() for ei in qs])
        self.debug("setting executable {}".format(self.executor.executable))

    def update_queues(self):
        self._update_queues()

    def update_info(self):
        try:
            self._update()
        except BaseException as e:
            self.debug_exception()
            self.warning_dialog("Failed updating info: Error={}".format(e))

    # ===============================================================================
    # info update
    # ===============================================================================
    def _get_all_automated_runs(self, qs=None):
        if qs is None:
            qs = self.experiment_queues

        return [ai for ei in qs for ai in ei.automated_runs if ai.executable]

    def _update(self, queues=None):
        self.debug("update runs")
        if queues is None:
            queues = self.experiment_queues

        queues = [qi for qi in queues if qi.is_updateable()]
        if not queues:
            return

        self.debug("executor executable {}".format(self.executor.executable))
        self.debug("updating stats, ")
        self.executor.stats.experiment_queues = queues
        self.executor.stats.calculate()

        self.refresh_executable(queues)

        self._set_analysis_metadata()

        self.debug("info updated")
        for qi in queues:
            qi.refresh_table_needed = True

    def _set_analysis_metadata(self):
        cache = dict()

        db = self.get_database()
        aruns = self._get_all_automated_runs()
        with db.session_ctx():
            for ai in aruns:
                if ai.skip:
                    continue

                ln = ai.labnumber
                if ln == "dg":
                    continue

                # is run in cache
                if ln not in cache:
                    info = db.get_identifier_info(ln)
                    self.debug("Info for {}={}".format(ln, info))
                    if not info:
                        cache[ln] = dict(identifier_error=True)
                    else:
                        info["identifier_error"] = False
                        cache[ln] = info

                ai.trait_set(**cache[ln])

    def execute_queues(self, queues):
        names = ",".join([e.name for e in queues])
        self.debug("queues: n={}, names={}".format(len(queues), names))

        self.executor.trait_set(experiment_queues=queues, experiment_queue=queues[0])

        return self.executor.execute()

    def verify_database_connection(self, inform=True):
        db = self.get_database()
        if db is not None:
            if db.connect(force=True):
                return True
        elif inform:
            self.warning_dialog("No Database available")

    def sync_queue(self, queue):
        ms = queue.mass_spectrometer
        ed = queue.extract_device
        db = self.get_database()
        with db.session_ctx():
            next_pos = None
            for i, ai in enumerate(queue.automated_runs):
                if ai.skip or ai.is_special():
                    continue

                kw = {
                    "identifier": ai.identifier,
                    "position": ai.position,
                    "mass_spectrometer": ms.lower(),
                    "extract_device": ed,
                }
                if ai.is_step_heat():
                    kw["aliquot"] = ai.aliquot
                    kw["extract_value"] = ai.extract_value

                self.debug("checking {}/{}. attr={}".format(i, ai.runid, kw))

                aa = db.get_analysis_by_attr(**kw)
                if aa is None:
                    self.debug("----- not found")
                    if next_pos == ai:
                        i -= 1
                        break
                    elif not self.confirmation_dialog(
                        "Found analyses up to {}. "
                        "position={}, extract={}. "
                        "Continue searching?".format(
                            ai.runid, ai.extract_value, ai.position
                        )
                    ):
                        break
                    next_pos = queue.automated_runs[i + 1]

            if i:
                if i == len(queue.automated_runs) - 1:
                    self.information_dialog(
                        "All Analyses from this experiment have been run"
                    )
                else:
                    queue.automated_runs = queue.automated_runs[i:]
            else:
                self.information_dialog(
                    "No Analyses from this experiment have been run"
                )

    # ===============================================================================
    # handlers
    # ===============================================================================
    def _experiment_queue_changed(self, eq):
        if eq:
            self.experiment_factory.queue = eq
            self.experiment_factory.sync_queue_meta()
            self.experiment_factory.edit_enabled = True
        else:
            self.experiment_factory.edit_enabled = False

    @on_trait_change("executor:experiment_queue")
    def _activate_editor(self, eq):
        self.activate_editor_event = id(eq)

    @on_trait_change("experiment_queues[]")
    def _update_queues(self):
        qs = self.experiment_queues
        self.executor.stats.experiment_queues = qs

    @on_trait_change("experiment_factory:run_factory:changed")
    def _queue_dirty(self):
        self.experiment_queue.changed = True

    @on_trait_change("experiment_queue:dclicked")
    def _dclicked_changed(self, new):
        self.experiment_factory.run_factory.edit_mode = True
        self._set_factory_runs(self.experiment_queue.selected)

    @on_trait_change("experiment_factory:run_factory:update_info_needed")
    def _refresh3(self):
        self.debug("update info needed fired")
        self.update_info()

    @on_trait_change("executor:queue_modified")
    def _refresh5(self, new):
        if new:
            self.debug("queue modified fired")
            self.update_info()

    @on_trait_change("experiment_factory:run_factory:refresh_table_needed")
    def _refresh4(self):
        for qi in self.experiment_queues:
            qi.refresh_table_needed = True

    @on_trait_change("experiment_factory:save_button")
    def _save_update(self):
        self.save_event = True
        self.update_info()

    @on_trait_change("experiment_queue:refresh_info_needed")
    def _handle_refresh(self):
        self.update_info()

    @on_trait_change("experiment_queue:selected")
    def _selected_changed(self, new):
        ef = self.experiment_factory
        rf = ef.run_factory
        rf.edit_mode = False
        if new:
            self._set_factory_runs(new)

            # if self.executor.is_alive():
            a = new[-1]
            if not a.skip:
                self.executor.stats.calculate_at(a, at_times=self.executor.is_alive())
                # self.stats.calculate()

    @on_trait_change("experiment_factory:queue_factory:delay_between_analyses")
    def handle_delay_between_analyses(self, new):
        if self.executor.is_alive():
            self.executor.experiment_queue.delay_between_analyses = new

    def _set_factory_runs(self, new):
        ef = self.experiment_factory
        rf = ef.run_factory
        # print 'set runs'
        # rf.special_labnumber = 'Special Labnumber'

        rf.suppress_update = True
        rf.set_selected_runs(new)
        rf.suppress_update = False

    def _executor_factory(self):
        e = ExperimentExecutor(mode=self.mode, application=self.application)
        e.bind_preferences()
        return e

    # ===============================================================================
    # defaults
    # ===============================================================================
    def _executor_default(self):
        return self._executor_factory()

    def _experiment_factory_default(self):
        dms = "Spectrometer"
        if self.application:
            p2 = (
                "pychron.spectrometer.base_spectrometer_manager.BaseSpectrometerManager"
            )
            spec = self.application.get_service(p2)
            if spec:
                dms = spec.name.capitalize()

        e = ExperimentFactory(
            application=self.application, dvc=self.dvc, default_mass_spectrometer=dms
        )
        return e


# ============= EOF =============================================
