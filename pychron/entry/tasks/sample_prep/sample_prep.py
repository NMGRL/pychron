# ===============================================================================
# Copyright 2016 Jake Ross
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
from pyface.constant import OK
from pyface.file_dialog import FileDialog
from traits.api import HasTraits, Str, Bool, Property, Button, on_trait_change, List, \
    cached_property, Instance, Event, Date, Enum, Long
from traitsui.api import View, UItem
# ============= standard library imports ========================
import os
import socket
import paramiko
# ============= local library imports  ==========================
from pychron.dvc.dvc_irradiationable import DVCAble

DEBUG = True


def get_sftp_client(host, user, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print host, user, password
    try:
        ssh.connect(host, username=user, password=password, timeout=2)
    except (socket.timeout, paramiko.AuthenticationException):
        return

    return ssh.open_sftp()


class SampleRecord(HasTraits):
    name = Str
    worker = Str
    session = Str
    project = Str
    material = Str
    grainsize = Str
    steps = List


class PrepStepRecord(HasTraits):
    id = Long
    crush = Str
    sieve = Str
    wash = Str
    acid = Str
    frantz = Str
    pick = Str
    heavy_liquid = Str

    flag_crush = Bool
    flag_sieve = Bool
    flag_wash = Bool
    flag_acid = Bool
    flag_frantz = Bool
    flag_pick = Bool
    flag_heavy_liquid = Bool

    status = Enum('', 'Good', 'Bad', 'Use For Irradiation')
    comment = Str

    edit_comment_button = Button
    crushed = Bool
    timestamp = Date

    @on_trait_change('flag_+')
    def _handle_flag(self, name, new):
        attr = name[5:]
        setattr(self, attr, 'X' if new else '')

    def _edit_comment_button_fired(self):
        v = View(UItem('comment', style='custom'),
                 title='Edit Comment',
                 resizable=True,
                 kind='livemodal',
                 buttons=['OK', 'Cancel', 'Revert'])

        self.edit_traits(view=v)


class SamplePrep(DVCAble):
    session = Str
    worker = Str
    sessions = Property(depends_on='worker, refresh_sessions')
    refresh_sessions = Event
    workers = List

    project = Str
    projects = Property(depends_on='principal_investigator')

    principal_investigator = Str
    principal_investigators = List

    samples = Property(depends_on='project')

    session_samples = List
    active_sample = Instance(SampleRecord, ())

    prep_step = Instance(PrepStepRecord, ())

    selected = List
    add_selection_button = Button
    add_session_button = Button
    add_worker_button = Button
    add_step_button = Button

    upload_image_button = Button
    selected_step = Instance(PrepStepRecord)

    def activated(self):

        self._load_pis()
        self._load_workers()

        if DEBUG:
            self.worker = self.workers[0]
            self.session = self.sessions[0]
            self.principal_investigator = 'MZimmerer'
            self.project = self.projects[0]

        self._load_session_samples()

    def prepare_destroy(self):
        pass

    # private
    def _add_session(self, obj, worker):
        self.dvc.add_sample_prep_session(obj.name, worker, obj.comment)

    def _add_worker(self, obj):
        self.dvc.add_sample_prep_worker(obj.name,
                                        obj.fullname,
                                        obj.email,
                                        obj.phone,
                                        obj.comment)

    def _load_session_samples(self):
        if self.worker and self.session:
            with self.dvc.session_ctx():
                ss = self.dvc.get_sample_prep_samples(self.worker, self.session)
                self.session_samples = [self._sample_record_factory(i) for i in ss]

    def _load_workers(self):
        self.workers = self.dvc.get_sample_prep_worker_names()

    def _load_pis(self):
        self.principal_investigators = self.dvc.get_principal_investigator_names()

    def _sample_record_factory(self, s):
        r = SampleRecord(name=s.name,
                         project=s.project.name,
                         material=s.material.name,
                         grainsize=s.material.grainsize or '',
                         worker=self.worker,
                         session=self.session)
        return r

    def _load_steps_for_sample(self, asample):
        with self.dvc.session_ctx():
            def factory(s):
                pstep = PrepStepRecord(id=s.id,
                                       crush=s.crush or '',
                                       sieve=s.sieve or '',
                                       wash=s.wash or '',
                                       acid=s.acid or '',
                                       frantz=s.frantz or '',
                                       pick=s.pick or '',
                                       heavy_liquid=s.heavy_liquid or '',
                                       timestamp=s.timestamp)
                return pstep

            asample.steps = [factory(i) for i in self.dvc.get_sample_prep_steps(asample.worker, asample.session,
                                                                                asample.name,
                                                                                asample.project,
                                                                                asample.material,
                                                                                asample.grainsize)]

    def _make_step(self):
        attrs = ('crush', 'wash', 'sieve', 'acid', 'frantz',
                 'heavy_liquid', 'pick', 'status', 'comment')
        d = {a: getattr(self.prep_step, a) for a in attrs}
        return d

    # def _upload_images(self, client, ps):
    #     root = self.application.preferences.get('pychron.entry.sample_prep.root')
    #     ims = []
    #     for p in ps:
    #         pp = os.path.join(root, os.path.basename(p))
    #         self.debug('putting {} {}'.format(p, pp))
    #         client.put(p, pp)
    #         ims.append(pp)
    #     return ims

    # handlers
    def _active_sample_changed(self, new):
        if new:
            self._load_steps_for_sample(new)

    def _add_step_button_fired(self):
        if self.active_sample:
            sa = (self.active_sample.name, self.active_sample.project,
                  self.active_sample.material, self.active_sample.grainsize)

            params = self._make_step()
            self.dvc.add_sample_prep_step(sa, self.worker, self.session,
                                          **params)
            self._load_steps_for_sample(self.active_sample)

    def _add_selection_button_fired(self):
        if self.selected:
            dvc = self.dvc
            for s in self.selected:
                sa = (s.name, s.project, s.material, s.grainsize)
                dvc.add_sample_prep_step(sa, self.worker, self.session, added=True)

            self._load_session_samples()

    def _add_session_button_fired(self):
        from pychron.entry.tasks.sample_prep.adder import AddSession
        s = AddSession()
        info = s.edit_traits()
        if info.result:
            if s.name:
                self._add_session(s, self.worker)
                self.refresh_sessions = True
                self.session = s.name

    def _add_worker_button_fired(self):
        from pychron.entry.tasks.sample_prep.adder import AddWorker
        a = AddWorker()
        info = a.edit_traits()
        if info.result:
            if a.name:
                self._add_worker(a)
                self._load_workers()
                self.worker = a.name

    def _session_changed(self):
        self._load_session_samples()

    def _selected_step_changed(self):
        print 'asdfsafd', self.selected_step, self.selected_step.id

    def _upload_image_button_fired(self):
        step = self.selected_step
        if step is None:
            step = self.active_sample.steps[0]
        if not step:
            return

        host = self.application.preferences.get('pychron.entry.sample_prep.host')
        username = self.application.preferences.get('pychron.entry.sample_prep.username')
        password = self.application.preferences.get('pychron.entry.sample_prep.password')
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(host, username=username, password=password, timeout=2)
        except (socket.timeout, paramiko.AuthenticationException):
            self.warning_dialog('Could not connect to Image Server')
            return

        client = ssh.open_sftp()

        dlg = FileDialog(action='open files')
        if dlg.open() == OK:
            if not dlg.paths:
                return

            root = self.application.preferences.get('pychron.entry.sample_prep.root')
            dvc = self.dvc
            for p in dlg.paths:
                pp = '{}/{}'.format(root, os.path.basename(p))
                self.debug('putting {} {}'.format(p, pp))
                client.put(p, pp)
                dvc.add_sample_prep_image(step.id, host, '{}/{}'.format(username, pp))

            client.close()

    @cached_property
    def _get_sessions(self):
        if self.worker:
            return self.dvc.get_sample_prep_session_names(self.worker)
        else:
            return []

    @cached_property
    def _get_samples(self):
        if self.project:
            with self.dvc.session_ctx():
                ss = self.dvc.get_samples(project=self.project)
                return [self._sample_record_factory(si) for si in ss]
        else:
            return []

    @cached_property
    def _get_projects(self):
        with self.dvc.session_ctx():
            ps = self.dvc.get_projects(principal_investigator=self.principal_investigator,
                                       order='asc')
            return [p.name for p in ps]

# ============= EOF =============================================
