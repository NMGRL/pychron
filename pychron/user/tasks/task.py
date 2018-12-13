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
from __future__ import absolute_import
import hashlib
import os

import yaml
from pyface.tasks.action.schema import SToolBar
from pyface.tasks.action.task_action import TaskAction
from pyface.tasks.task_layout import TaskLayout
from traits.api import HasTraits, List, Str, Bool, Enum, on_trait_change
from traits.api import Instance

from pychron.core.pychron_traits import EmailStr
from pychron.envisage.resources import icon
from pychron.envisage.tasks.base_task import BaseTask
from pychron.paths import paths
from pychron.pychron_constants import DVC_PROTOCOL
from pychron.user.tasks.panes import UsersPane, NewUserView


class User(HasTraits):
    name = Str
    email = Str
    enabled = Bool
    keys = ('name', 'email', 'enabled')

    def __init__(self, dbrecord, *args, **kw):
        super(User, self).__init__(*args, **kw)
        self.name = dbrecord.name
        self.email = dbrecord.email or ''


class NewUserAction(TaskAction):
    name = 'New'
    image = icon('user-new-2')
    method = 'new_user'


class UsersTask(BaseTask):
    name = 'Users'
    users = List
    ousers = List
    filter_attribute = Enum('name', 'email')
    filter_str = Str

    new_user_name = Str
    new_user_email = EmailStr

    tool_bars = [SToolBar(NewUserAction())]
    db = Instance('pychron.dvc.dvc_database.DVCDatabase')
    id = 'pychron.users'
    _hash = None
    auto_save = False

    def prepare_destroy(self):
        self.auto_save = False

    def create_central_pane(self):
        up = UsersPane(model=self)
        return up

    def activated(self):
        db = self.db
        if db:
            if not db.connect():
                return

            self.load_users()

    def load_users(self):
        users = [User(user) for user in self.db.get_users()]
        self._sync(users)
        self._hash = self._generate_hash(users)

        self.users = users
        self.ousers = self.users[:]

    def new_user(self):
        info = self.edit_traits(view=NewUserView, kind='livemodal')
        if info.result:
            if not self.db.get_user(self.new_user_name):
                self.db.add_user(self.new_user_name, email=self.new_user_email)
                self.load_users()
            else:
                self.information_dialog('User "{}" already exists'.format(self.new_user_name))

    def _sync(self, users):
        path = os.path.join(paths.setup_dir, 'users.yaml')
        if os.path.isfile(path):
            with open(path, 'r') as rfile:
                yl = yaml.load(rfile)
                for yi in yl:
                    uu = next((i for i in users if i.name == yi.get('name')), None)
                    if uu:
                        uu.enabled = yi.get('enabled')

    def _generate_hash(self, users):
        md5 = hashlib.md5()
        for u in users:
            for k in User.keys:
                md5.update(str(getattr(u, k)).encode('utf-8'))
        return md5.hexdigest()

    def _save(self):
        db = self.db
        if db:
            for user in self.ousers:
                dbuser = db.get_user(user)
                for k in user.keys:
                    setattr(dbuser, k, getattr(user, k))
            db.commit()

        # dump to users.yaml
        path = os.path.join(paths.setup_dir, 'users.yaml')
        with open(path, 'w') as wfile:
            yl = [{'name': i.name, 'email': i.email, 'enabled': i.enabled} for i in self.ousers]
            yaml.dump(yl, wfile, default_flow_style=False)

        self._hash = self._generate_hash(self.ousers)
        return True

    def _prompt_for_save(self):
        if self._hash != self._generate_hash(self.ousers):
            message = 'You have unsaved changes. Save changes to Database?'
            ret = self._handle_prompt_for_save(message)
            if ret == 'save':
                return self._save()
            return ret
        return True

    @on_trait_change('users:[enabled]')
    def _handle(self):
        if self.auto_save:
            self._save()

    def _filter_str_changed(self):
        self.users = [u for u in self.ousers
                      if getattr(u, self.filter_attribute).lower().startswith(self.filter_str)]

    def _default_layout_default(self):
        return TaskLayout()

    def _db_default(self):
        app = self.application
        d = app.get_service(DVC_PROTOCOL)
        d.db.create_session()
        return d.db
# ============= EOF =============================================
