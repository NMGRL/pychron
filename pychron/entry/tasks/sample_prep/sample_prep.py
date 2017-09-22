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
import os
import socket

import paramiko
from pyface.constant import OK
from pyface.file_dialog import FileDialog
from traits.api import HasTraits, Str, Bool, Property, Button, on_trait_change, List, cached_property, \
    Instance, Event, Date, Enum, Long, Any, Int
from traitsui.api import View, UItem, Item, EnumEditor

from pychron.core.helpers.datetime_tools import get_date
from pychron.dvc.dvc_irradiationable import DVCAble
from pychron.entry.tasks.sample_prep.sample_locator import SampleLocator
from pychron.image.camera import CameraViewer
from pychron.image.viewer import ImageViewer
from pychron.paths import paths
from pychron.persistence_loggable import PersistenceMixin

DEBUG = False


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

    def has_step(self, step):
        for si in self.steps:
            if getattr(si, step):
                return True


class PrepStepRecord(HasTraits):
    id = Long
    crush = Str
    sieve = Str
    wash = Str
    acid = Str
    frantz = Str
    pick = Str
    heavy_liquid = Str

    nimages = Int

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


class SamplePrep(DVCAble, PersistenceMixin):
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
    edit_session_button = Button

    snapshot_button = Button('Snapshot')
    view_image_button = Button
    view_camera_button = Button
    upload_image_button = Button
    selected_step = Instance(PrepStepRecord)
    dclicked = Event

    pattributes = ('worker', 'session', 'principal_investigator', 'project')
    move_to_session_name = Str
    move_to_sessions = List

    fcrush = Bool
    fsieve = Bool
    fwash = Bool
    facid = Bool
    ffrantz = Bool
    fheavy_liquid = Bool
    fpick = Bool
    fstatus = Enum('', 'Good', 'Bad', 'Use For Irradiation')
    camera = Any
    selected_image = Any

    @property
    def persistence_path(self):
        return os.path.join(paths.hidden_dir, 'sample_prep')

    def activated(self):

        self.dvc.create_session()
        self._load_pis()
        self._load_workers()

        self.load()

        if DEBUG:
            self.worker = self.workers[0]
            self.session = self.sessions[0]
            self.principal_investigator = 'MZimmerer'
            self.project = self.projects[0]

        self._load_session_samples()

        self.camera = CameraViewer()
        # self.camera = ToupCamCamera()
        self.camera.activate()

    def prepare_destroy(self):
        self.dvc.close_session()
        self.dump()
        self.camera.close()

    def locate_sample(self):
        locator = SampleLocator(dvc=self.dvc)
        info = locator.edit_traits()
        if info.result:
            if locator.session:
                self.worker = locator.session.worker_name
                self.session = locator.session.name

    def move_to_session(self):
        nsession = self._get_new_session()
        if nsession:
            s = self.active_sample
            sd = {'name': s.name, 'material': s.material, 'project': s.project}

            self.dvc.move_sample_to_session(self.session, sd, nsession, self.worker)
            self.active_sample = SampleRecord()
            self._load_session_samples()

    # private
    def _get_new_session(self):

        self.move_to_sessions = [s for s in self.sessions if s != self.session]

        v = View(Item('move_to_session_name',
                      editor=EnumEditor(name='move_to_sessions')),
                 title='Move to Session',
                 buttons=['OK', 'Cancel'],
                 resizable=True, kind='livemodal')

        info = self.edit_traits(v)
        if info.result:
            return self.move_to_session_name

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
            ss = self.dvc.get_sample_prep_samples(self.worker, self.session)
            self.session_samples = [self._sample_record_factory(i) for i in ss]
            self.osession_samples = self.session_samples

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
        def factory(s):
            pstep = PrepStepRecord(id=s.id,
                                   crush=s.crush or '',
                                   sieve=s.sieve or '',
                                   wash=s.wash or '',
                                   acid=s.acid or '',
                                   frantz=s.frantz or '',
                                   pick=s.pick or '',
                                   heavy_liquid=s.heavy_liquid or '',
                                   timestamp=s.timestamp,
                                   nimages=len(s.images))
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
    @on_trait_change('fcrush, fsieve, fwash, facid, ffrantz, fheavy_liquid, fpick, fstatus')
    def _handle_filter(self):
        def test(si):
            r = [si.has_step(f) for f in ('crush', 'sieve', 'wash', 'acid', 'heavy_liquid', 'pick', 'status')
                 if getattr(self, 'f{}'.format(f))]
            return all(r)

        self.session_samples = [s for s in self.osession_samples if test(s)]

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

    def _edit_session_button_fired(self):
        oname = self.session
        from pychron.entry.tasks.sample_prep.adder import AddSession
        s = AddSession(title='Edit Selected Session')
        obj = self.dvc.get_sample_prep_session(self.session, self.worker)
        s.name = obj.name
        s.comment = obj.comment
        self.dvc.db.commit()

        info = s.edit_traits()
        if info.result:
            kw = {'comment': s.comment}
            if s.name != oname:
                kw['name'] = s.name

            self.dvc.update_sample_prep_session(oname, self.worker, **kw)
            self.refresh_sessions = True
            self.session = s.name

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

    @on_trait_change('camera:snapshot_event')
    def _handle_snapshot(self, meta):
        step, msm = self._pre_image()
        sessionname = self.session.replace(' ', '_')

        dvc = self.dvc
        name = meta.get('name', True)
        if isinstance(name, bool):
            name = '{}-{}-{}'.format(self.active_sample.name, step.id, get_date(fmt='%Y-%m-%d%H%M'))

        pp = os.path.join('images', 'sampleprep', sessionname, '{}.jpg'.format(name))
        from tempfile import TemporaryFile
        p = TemporaryFile()
        # p='{}.jpg'.format(p)
        self.camera.save_jpeg(p)
        p.seek(0)
        url = msm.put(p, pp)
        print 'moving to {}'.format(pp)
        dvc.add_sample_prep_image(step.id, msm.get_host(), url, meta.get('note', ''))

    def _view_camera_button_fired(self):
        # v = View(VGroup(UItem('camera',
        #                       width=640, height=480,
        #                       editor=CameraEditor()),
        #                 UItem('snapshot_button')),
        #                 title='Camera')
        #
        # self.edit_traits(view=v)
        # self.camera.activate()
        self.camera.edit_traits()

    def _dclicked_fired(self):
        self._view_associated_image()

    def _selected_step_changed(self, new):
        pass

    def _view_image_button_fired(self):
        self._view_associated_image()

    def _view_associated_image(self):

        new = self.selected_step
        if new:
            msm = self._get_msm()
            if not msm:
                return

            dvc = self.dvc
            with dvc.session_ctx():
                step = dvc.get_sample_prep_step_by_id(new.id)
                if step.images:
                    # dbimg = step.images[0]
                    #
                    # buf = StringIO.StringIO()
                    # msm.get(dbimg.path, buf)
                    # buf.seek(0)
                    # img = Image.open(buf)
                    # self.selected_image = img.convert('RGBA')
                    v = ImageViewer(image_getter=msm,
                                    title='{} Images'.format(self.active_sample.name))
                    v.set_images([(img.path, img.note) for img in step.images])
                    v.edit_traits()

            #
            # self.edit_traits(view=v)

    def _get_msm(self):
        msm = self.application.get_service('pychron.media_storage.manager.MediaStorageManager')
        if not msm:
            self.warning_dialog('Media Storage Plugin is required. Please enable and try again')
        return msm

    def _pre_image(self):
        step = self.selected_step
        if step is None and self.active_sample.steps:
            step = self.active_sample.steps[0]

        if not step:
            self.warning_dialog('Select a prep step to associate with the image')

            return

        msm = self._get_msm()

        return step, msm

    def _upload_image_button_fired(self):
        step, msm = self._pre_image()

        # host = self.application.preferences.get('pychron.entry.sample_prep.host')
        # username = self.application.preferences.get('pychron.entry.sample_prep.username')
        # password = self.application.preferences.get('pychron.entry.sample_prep.password')

        # ssh = paramiko.SSHClient()
        # ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # try:
        #     ssh.connect(host, username=username, password=password, timeout=2)
        # except (socket.timeout, paramiko.AuthenticationException):
        #     self.warning_dialog('Could not connect to Image Server')
        #     return
        #
        # client = ssh.open_sftp()

        sessionname = self.session.replace(' ', '_')
        dlg = FileDialog(action='open files')
        if dlg.open() == OK:
            if not dlg.paths:
                return

            # root = self.application.preferences.get('pychron.entry.sample_prep.root')
            dvc = self.dvc
            for p in dlg.paths:
                pp = '{}/{}'.format(sessionname, os.path.basename(p))
                self.debug('putting {} {}'.format(p, pp))
                url = msm.put(p, pp)
                # client.put(p, pp)
                dvc.add_sample_prep_image(step.id, msm.get_host(), url)

                # client.close()

    @cached_property
    def _get_sessions(self):
        if self.worker:
            return self.dvc.get_sample_prep_session_names(self.worker)
        else:
            return []

    @cached_property
    def _get_samples(self):
        if self.project:
            ss = self.dvc.get_samples(projects=self.project, principal_investigators=self.principal_investigator)
            return [self._sample_record_factory(si) for si in ss]
        else:
            return []

    @cached_property
    def _get_projects(self):
        with self.dvc.session_ctx(use_parent_session=False):

            ps = self.dvc.get_projects(principal_investigators=(self.principal_investigator,),
                                       order='asc')
            self.project = ''
            if ps:
                return [p.name for p in ps]
            else:
                return []

# ============= EOF =============================================
