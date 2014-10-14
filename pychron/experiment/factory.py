# ===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import Instance, Button, Bool, Property, \
    on_trait_change, String, Any, DelegatesTo, List, Str
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.experiment.automated_run.uv.factory import UVAutomatedRunFactory
from pychron.experiment.automated_run.factory import AutomatedRunFactory
from pychron.experiment.queue.factory import ExperimentQueueFactory
from pychron.experiment.queue.experiment_queue import ExperimentQueue
from pychron.experiment.undoer import ExperimentUndoer
from pychron.pychron_constants import LINE_STR
from pychron.experiment.utilities.identifier import convert_extract_device
from pychron.loggable import Loggable
from pychron.consumer_mixin import ConsumerMixin
from pychron.lasers.laser_managers.ilaser_manager import ILaserManager


class ExperimentFactory(Loggable, ConsumerMixin):
    db = Any
    run_factory = Instance(AutomatedRunFactory)
    queue_factory = Instance(ExperimentQueueFactory)
    undoer = Instance(ExperimentUndoer)

    add_button = Button('Add')
    clear_button = Button('Clear')
    save_button = Button('Save')
    edit_mode_button = Button('Edit')
    edit_enabled = DelegatesTo('run_factory')

    auto_increment_id = Bool(False)
    auto_increment_position = Bool(False)

    queue = Instance(ExperimentQueue, ())

    ok_add = Property(depends_on='_mass_spectrometer, _extract_device, _labnumber, _username')

    _username = String
    _mass_spectrometer = String
    extract_device = String
    _labnumber = String

    selected_positions = List
    default_mass_spectrometer = Str

    _load_persistence_flag = False
    #===========================================================================
    # permisions
    #===========================================================================
    #    max_allowable_runs = Int(10000)
    #    can_edit_scripts = Bool(True)

    def __init__(self, *args, **kw):
        super(ExperimentFactory, self).__init__(*args, **kw)
        self.setup_consumer(self._add_run, main=True)

    def undo(self):
        self.info('undo')
        self.undoer.undo()

    def sync_queue_meta(self):
        self.debug('syncing queue meta')
        eq = self.queue
        qf = self.queue_factory
        for a in ('username', 'mass_spectrometer', 'extract_device',
                  'load_name',
                  'delay_before_analyses','delay_between_analyses',
                  'queue_conditionals_name'):

            if not self._sync_queue_to_factory(eq, qf, a):
                self._sync_factory_to_queue(eq, qf, a)

        self.debug('run factory set mass spec {}'.format(self._mass_spectrometer))
        self.run_factory.set_mass_spectrometer(self._mass_spectrometer)

    def _sync_queue_to_factory(self, eq, qf, a):
        v = getattr(eq, a)
        if isinstance(v, str):
            v = v.strip()

        if v:
            self.debug('sync queue to factory {}>>{}'.format(a,v))
            setattr(qf, a, v)
            return True

    def _sync_factory_to_queue(self, eq, qf, a):
        v = getattr(qf, a)
        if isinstance(v, str):
            v = v.strip()
            if v:
                self.debug('sync factory to queue {}>>{}'.format(a,v))
                setattr(eq, a, v)

    def activate(self, load_persistence=True):
        self._load_persistence_flag=load_persistence

        self.queue_factory.activate(load_persistence)
        self.run_factory.activate(load_persistence)

    def destroy(self):
        self._should_consume = False
        self.run_factory.deactivate()
        self.queue_factory.deactivate()

    def set_selected_runs(self, runs):
        self.run_factory.set_selected_runs(runs)

    def _add_run(self, *args, **kw):
        positions = [str(pi.positions[0]) for pi in self.selected_positions]

        load_name = self.queue_factory.load_name

        q = self.queue
        rf = self.run_factory
        new_runs, freq = rf.new_runs(q, positions=positions,
                                     auto_increment_position=self.auto_increment_position,
                                     auto_increment_id=self.auto_increment_id)
        if new_runs:
            aruns = q.automated_runs
            if q.selected:
                idx = aruns.index(q.selected[-1])
            else:
                idx = len(aruns) - 1

            runs = q.add_runs(new_runs, freq,
                              freq_before=rf.freq_before,
                              freq_after=rf.freq_after,
                              is_run_block=rf.run_block_enabled)

            self.undoer.push('add runs', runs)

            idx += len(runs)

            with rf.update_selected_ctx():
                q.select_run_idx(idx)

    #===============================================================================
    # handlers
    #===============================================================================
    def _clear_button_fired(self):
        self.queue.clear_frequency_runs()

    def _add_button_fired(self):
        """
            only allow add button to be fired every 0.5s

            use consumermixin.add_consumable instead of frequency limiting
        """
        self.add_consumable(5)

    def _edit_mode_button_fired(self):
        self.run_factory.edit_mode = not self.run_factory.edit_mode

        #@on_trait_change('run_factory:clear_end_after')
        #def _clear_end_after(self, new):
        #    print 'enadfas', new

    def _update_end_after(self, new):
        if new:
            for ai in self.queue.automated_runs:
                ai.end_after = False

        self.run_factory.set_end_after(new)

    def _queue_changed(self, new):
        self.undoer.queue = new

    @on_trait_change('''queue_factory:[mass_spectrometer,
extract_device, delay_+, tray, username, load_name, email, queue_conditionals_name]''')
    def _update_queue(self, name, new):
        self.debug('update queue {}={}'.format(name,new))
        if name == 'mass_spectrometer':
            self.debug('_update_queue "{}"'.format(new))
            self._mass_spectrometer = new
            self.run_factory.set_mass_spectrometer(new)

        elif name == 'extract_device':
            self._set_extract_device(new)
        elif name == 'username':
            self._username = new
            # elif name=='email':
            #     self.email=new
            #            self.queue.username = new

        if self.queue:
            self.queue.trait_set(**{name: new})

        self.queue.changed = True

    #===============================================================================
    # private
    #===============================================================================
    def _set_extract_device(self, ed):
        self.debug('setting extract dev="{}" mass spec="{}"'.format(ed, self._mass_spectrometer))
        self.extract_device = ed
        self.run_factory = self._run_factory_factory()

        self.run_factory.setup_files()
        self.run_factory.set_mass_spectrometer(self._mass_spectrometer)

        if self._load_persistence_flag:
            self.run_factory.load()

        if self.queue:
            self.queue.set_extract_device(ed)
            self.queue.username = self._username
            self.queue.mass_spectrometer = self._mass_spectrometer

    def _get_patterns(self, ed):
        ps = []
        service_name = convert_extract_device(ed)
        #service_name = ed.replace(' ', '_').lower()
        man = self.application.get_service(ILaserManager, 'name=="{}"'.format(service_name))
        if man:
            ps = man.get_pattern_names()
        else:
            self.debug('No remote patterns. {} ({}) not available'.format(ed, service_name))

        return ps

    #===============================================================================
    # property get/set
    #===============================================================================
    def _get_ok_add(self):
        """
        """
        uflag = bool(self._username)
        msflag = not self._mass_spectrometer in ('', 'Spectrometer',LINE_STR)
        ret = uflag and msflag
        if self.run_factory.run_block in ('RunBlock',LINE_STR):
            ret = ret and self._labnumber
        return ret

    #===============================================================================
    #
    #===============================================================================
    def _run_factory_factory(self):
        if self.extract_device == 'Fusions UV':
            klass = UVAutomatedRunFactory
        else:
            klass = AutomatedRunFactory

        rf = klass(db=self.db,
                   application=self.application,
                   extract_device=self.extract_device,
                   mass_spectrometer=self.default_mass_spectrometer)

        # rf.activate()
        rf.on_trait_change(lambda x: self.trait_set(_labnumber=x), 'labnumber')
        rf.on_trait_change(self._update_end_after, 'end_after')

        return rf

    #    def _can_edit_scripts_changed(self):
    #        self.run_factory.can_edit = self.can_edit_scripts

    #===============================================================================
    # defaults
    #===============================================================================
    def _undoer_default(self):
        return ExperimentUndoer(run_factory=self.run_factory,
                                queue=self.queue)

    def _run_factory_default(self):
        return self._run_factory_factory()

    def _queue_factory_default(self):
        eq = ExperimentQueueFactory(db=self.db)
        # eq.activate()
        return eq

    def _db_changed(self):
        self.queue_factory.db = self.db
        self.run_factory.db = self.db

    def _application_changed(self):
        self.run_factory.application = self.application

    def _default_mass_spectrometer_changed(self):
        self.debug('default mass spec changed "{}"'.format(self.default_mass_spectrometer))
        self.run_factory.set_mass_spectrometer(self.default_mass_spectrometer)
        self.queue_factory.mass_spectrometer = self.default_mass_spectrometer
        self._mass_spectrometer = self.default_mass_spectrometer

        #============= EOF =============================================
