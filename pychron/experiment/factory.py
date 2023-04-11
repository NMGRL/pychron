# ===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import Instance, Button, Bool, Property, DelegatesTo, List, Str

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.pychron_traits import PositiveInteger
from pychron.dvc.dvc_irradiationable import DVCAble
from pychron.experiment.automated_run.cryo.factory import CryoAutomatedRunFactory
from pychron.experiment.automated_run.factory import AutomatedRunFactory
from pychron.experiment.automated_run.uv.factory import UVAutomatedRunFactory
from pychron.experiment.queue.experiment_queue import ExperimentQueue
from pychron.experiment.queue.factory import ExperimentQueueFactory
from pychron.experiment.undoer import ExperimentUndoer
from pychron.experiment.utilities.identifier import convert_extract_device
from pychron.lasers.laser_managers.ilaser_manager import ILaserManager
from pychron.pychron_constants import LINE_STR, CRYO, FUSIONS_UV


class ExperimentFactory(DVCAble):
    run_factory = Instance(AutomatedRunFactory)
    queue_factory = Instance(ExperimentQueueFactory)
    undoer = Instance(ExperimentUndoer)

    generate_queue_button = Button
    edit_queue_config_button = Button
    loading_manager = Instance("pychron.loading.loading_manager.LoadingManager")

    add_button = Button("Add")
    clear_button = Button("Clear")
    save_button = Button("Save")
    edit_mode_button = Button("Edit")
    edit_enabled = DelegatesTo("run_factory")

    auto_increment_id = Bool(False)
    auto_increment_id_count = PositiveInteger(1)
    auto_increment_position = Bool(False)

    queue = Instance(ExperimentQueue, ())

    ok_add = Property(
        depends_on="mass_spectrometer, extract_device, labnumber, username, load_name"
    )

    labnumber = DelegatesTo("run_factory")
    load_name = DelegatesTo("queue_factory")
    username = DelegatesTo("queue_factory")
    mass_spectrometer = DelegatesTo("queue_factory")
    extract_device = DelegatesTo("queue_factory")

    selected_positions = List
    default_mass_spectrometer = Str

    _load_persistence_flag = False

    # ===========================================================================
    # permisions
    # ===========================================================================
    # max_allowable_runs = Int(10000)
    # can_edit_scripts = Bool(True)

    # def __init__(self, *args, **kw):
    #     super(ExperimentFactory, self).__init__(auto_setup=False, *args, **kw)

    def activate(self, load_persistence=True):
        self._load_persistence_flag = load_persistence
        self.queue_factory.activate(load_persistence)
        self.run_factory.activate(load_persistence)

    def destroy(self):
        self.run_factory.deactivate()
        self.queue_factory.deactivate()

    def undo(self):
        self.info("undo")
        self.undoer.undo()

    def sync_queue_meta(self):
        self.debug("syncing queue meta")
        eq = self.queue
        qf = self.queue_factory
        for a in (
            "username",
            "mass_spectrometer",
            "extract_device",
            "email",
            "use_email",
            "use_group_email",
            "load_name",
            "tray",
            "delay_after_blank",
            "delay_between_analyses",
            "delay_after_air",
            "default_lighting",
            "queue_conditionals_name",
            "note",
        ):
            if not self._sync_queue_to_factory(eq, qf, a):
                self._sync_factory_to_queue(eq, qf, a)

        self.debug("run factory set mass spec {}".format(self.mass_spectrometer))
        self.run_factory.set_mass_spectrometer(self.mass_spectrometer)

    def set_selected_runs(self, runs):
        self.run_factory.set_selected_runs(runs)

    def get_patterns(self):
        return self._get_patterns(self.extract_device)

    # ===============================================================================
    # private
    # ===============================================================================
    def _sync_queue_to_factory(self, eq, qf, a):
        v = getattr(eq, a)
        if isinstance(v, str):
            v = v.strip()

        if v:
            self.debug("sync queue to factory {}>>{}".format(a, v))
            try:
                setattr(qf, a, v)
            except BaseException:
                self.debug(
                    "failed to sync queue to factory attr={} value={}".format(a, v)
                )
                self.debug_exception()
            return True

    def _sync_factory_to_queue(self, eq, qf, a):
        v = getattr(qf, a)
        if isinstance(v, str):
            v = v.strip()

        if v:
            self.debug("sync factory to queue {}>>{}".format(a, v))
            try:
                setattr(eq, a, v)
            except BaseException:
                self.debug(
                    "failed to sync factory to queue attr={} value={}".format(a, v)
                )
                self.debug_exception()

    def _add_run(self, *args, **kw):
        if not self.ok_add:
            missing = []
            if not bool(self.username):
                missing.append('"Username"')
            if self.mass_spectrometer in ("", "Spectrometer", LINE_STR):
                missing.append('"Spectrometer"')
            if self.extract_device not in ("", "Extact Device", LINE_STR):
                if not bool(self.queue_factory.load_name):
                    missing.append('"Load"')
            if self.run_factory.run_block in ("RunBlock", LINE_STR):
                if not self.labnumber:
                    missing.append('"Identifier"')

            f = "a value"
            if len(missing) > 1:
                f = "values"
            self.warning_dialog("Please set {} for {}".format(f, ",".join(missing)))
            return

        positions = [str(pi.positions[0]) for pi in self.selected_positions]
        self.debug("add run positions= {}".format(positions))

        q = self.queue
        rf = self.run_factory
        new_runs, freq = rf.new_runs(
            q,
            positions=positions,
            auto_increment_position=self.auto_increment_position,
            auto_increment_id=self.auto_increment_id_count
            if self.auto_increment_id
            else 0,
        )

        if new_runs:
            aruns = q.automated_runs
            if q.selected and q.selected[-1] in aruns:
                idx = aruns.index(q.selected[-1])
            else:
                idx = len(aruns) - 1

            runs = q.add_runs(new_runs, freq, is_run_block=rf.run_block_enabled)

            self.undoer.push("add runs", runs)

            idx += len(runs)

            with rf.update_selected_ctx():
                q.select_run_idx(idx)

            q.changed = True

    def _update_end_after(self, new):
        if new:
            for ai in self.queue.automated_runs:
                ai.end_after = False

        self.run_factory.set_end_after(new)

    def _update_queue(self, name, new):
        self.debug("update queue {}={}".format(name, new))
        if self.queue:
            self.queue.trait_set(**{name: new})
            self.queue.changed = True
            if name == "repository_identifier":
                for a in self.queue.automated_runs:
                    a.repository_identifier = new

        if name == "mass_spectrometer":
            self.mass_spectrometer = new
            self.run_factory.set_mass_spectrometer(new)

        elif name == "extract_device":
            self._set_extract_device(new)

        self._auto_save()

    def _auto_save(self):
        self.queue.auto_save()

    def _set_extract_device(self, ed):
        self.debug(
            'setting extract dev="{}" mass spec="{}"'.format(ed, self.mass_spectrometer)
        )
        self.run_factory = self._run_factory_factory()

        self.run_factory.remote_patterns = patterns = self._get_patterns(ed)
        self.run_factory.setup_files()

        if self._load_persistence_flag:
            self.run_factory.load()

        if self.queue:
            self.queue.set_extract_device(ed)
            self.queue.username = self.username
            self.queue.mass_spectrometer = self.mass_spectrometer
            self.queue.patterns = patterns

    def _get_patterns(self, ed):
        ps = []
        service_name = convert_extract_device(ed)
        man = self.application.get_service(
            ILaserManager, 'name=="{}"'.format(service_name)
        )
        if man:
            ps = man.get_pattern_names()
        else:
            self.debug(
                "No remote patterns. {} ({}) not available".format(ed, service_name)
            )

        return ps

    # ===============================================================================
    # handlers
    # ===============================================================================
    def _generate_queue_button_fired(self):
        """

        :return:
        """
        lm = self.loading_manager
        if lm:
            if self.load_name:
                positions = lm.get_positions_for_load(self.load_name)
                if positions:
                    runs = [self.run_factory.new_run_simple(*p) for p in positions]
                    self.queue.extend_runs(runs)
                    self.queue.changed = True

            else:
                self.warning_dialog("Please set a load")
        else:
            self.warning_dialog("Loading Plugin required to auto generate queues")

    def _clear_button_fired(self):
        self.queue.clear_frequency_runs()

    def _add_button_fired(self):
        """ """
        self.debug("add run fired")
        self._add_run()

    def _edit_mode_button_fired(self):
        self.run_factory.edit_mode = not self.run_factory.edit_mode

    # @on_trait_change('run_factory.apply_stepheat')
    def _apply_stepheat(self):
        self.run_factory.do_apply_stepheat(self.queue)

    def _queue_changed(self, new):
        self.undoer.queue = new

    def _dvc_changed(self):
        self.queue_factory.dvc = self.dvc
        self.run_factory.dvc = self.dvc

    def _application_changed(self):
        self.run_factory.application = self.application
        self.queue_factory.application = self.application

    def _default_mass_spectrometer_changed(self):
        self.debug(
            'default mass spec changed "{}"'.format(self.default_mass_spectrometer)
        )
        self.run_factory.set_mass_spectrometer(self.default_mass_spectrometer)
        self.queue_factory.mass_spectrometer = self.default_mass_spectrometer
        self.mass_spectrometer = self.default_mass_spectrometer

    # ===============================================================================
    # property get/set
    # ===============================================================================
    def _get_ok_add(self):
        """ """
        uflag = bool(self.username)
        msflag = self.mass_spectrometer not in ("", "Spectrometer", LINE_STR)
        lflag = True
        if self.extract_device not in ("", "Extract Device", LINE_STR):
            lflag = bool(self.queue_factory.load_name)

        ret = uflag and msflag and lflag
        if self.run_factory.run_block in ("RunBlock", LINE_STR):
            ret = ret and self.labnumber
        return ret

    # ===============================================================================
    #
    # ===============================================================================
    def _run_factory_factory(self):
        if self.extract_device == FUSIONS_UV:
            klass = UVAutomatedRunFactory
        elif self.extract_device == CRYO:
            klass = CryoAutomatedRunFactory
        else:
            klass = AutomatedRunFactory

        rf = klass(
            dvc=self.dvc,
            application=self.application,
            extract_device=self.extract_device,
            mass_spectrometer=self.mass_spectrometer,
        )

        rf.on_trait_change(self._update_end_after, "end_after")
        rf.on_trait_change(self._auto_save, "auto_save_needed")
        rf.on_trait_change(self._apply_stepheat, "apply_stepheat")

        return rf

    # ===============================================================================
    # defaults
    # ===============================================================================
    def _undoer_default(self):
        return ExperimentUndoer(run_factory=self.run_factory, queue=self.queue)

    def _run_factory_default(self):
        return self._run_factory_factory()

    def _queue_factory_default(self):
        eq = ExperimentQueueFactory(dvc=self.dvc, application=self.application)

        eq.on_trait_change(
            self._update_queue,
            """mass_spectrometer,
extract_device, delay_+, tray, username, load_name, note,
email, use_email, use_group_email,
queue_conditionals_name, repository_identifier""",
        )
        return eq


# ============= EOF =============================================
# def _gen_func(self, pd, ans):
#     import time
#
#     pd.max = 100
#     self.debug('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ generate queue')
#     auto_gen_config = self.auto_gen_config
#
#     # gen = self._generate_runs_from_load()
#     q = self.queue
#     rf = self.run_factory
#     rf.suppress_meta = True
#
#     def add_special(ln):
#         # tt = time.time()
#         pd.change_message('Add special: {}'.format(ln))
#         rf.special_labnumber = ln
#         new_runs, _ = rf.new_runs(q)
#         q.add_runs(new_runs, 0)
#         # rf.special_labnumber = ''
#         # print 'add special {}, {}'.format(ln, time.time()-tt)
#
#     st = time.time()
#     rb = auto_gen_config.end_run_block
#     if rb and rb in rf.run_blocks:
#         rf.run_block = auto_gen_config.end_run_block
#         new_runs, _ = rf.new_runs(q)
#         q.add_runs(new_runs, 0, is_run_block=False)
#
#     for ln, tag in (('Air', 'air'),
#                     ('Cocktail', 'cocktail'),
#                     ('Blank Unknown', 'blank')):
#
#         if getattr(auto_gen_config, 'start_{}'.format(tag)):
#             add_special(ln)
#
#     # for i, (labnumber, sample, position) in enumerate(gen()):
#     for i, (labnumber, sample, position) in enumerate(ans):
#         if i:
#             for ln, tag in (('Blank Unknown', 'blank'),
#                             ('Air', 'air'),
#                             ('Cocktail', 'cocktail')):
#                 f = getattr(auto_gen_config, '{}_freq'.format(tag))
#                 if f and i % f == 0:
#                     add_special(ln)
#
#         pd.change_message('Adding {}. Position: {}'.format(labnumber, position))
#
#         # tt = time.time()
#         rf.labnumber = labnumber
#         rf.sample = sample
#         # print 'set ln/sample {} {}'.format(labnumber, time.time()-tt)
#
#         new_runs, _ = rf.new_runs(q, positions=position)
#         # print 'new runs {} {}'.format(labnumber, time.time()-tt)
#
#         q.add_runs(new_runs, 0, is_run_block=False)
#         # print 'add runs {} {}'.format(labnumber, time.time()-tt)
#
#     for ln, tag in (('Blank Unknown', 'blank'),
#                     ('Air', 'air'),
#                     ('Cocktail', 'cocktail')):
#
#         if getattr(auto_gen_config, 'end_{}'.format(tag)):
#             add_special(ln)
#
#     rb = auto_gen_config.end_run_block
#     if rb and rb in rf.run_blocks:
#         rf.run_block = auto_gen_config.end_run_block
#         new_runs, _ = rf.new_runs(q)
#         q.add_runs(new_runs, 0, is_run_block=False)
#
#     # print 'finished adding', time.time()-st
#     q.changed = True
#     rf.update_info_needed = True
#     rf.suppress_meta = False
#     print('totaltime', time.time() - st)
#     pd.close()
#     rf.labnumber = ''
#     rf.sample = ''
