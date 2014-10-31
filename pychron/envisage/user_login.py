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
import os
import pickle
from traits.api import HasTraits, Button, List, Str
from traitsui.api import View, Item, HGroup, UItem, Label, Handler
# ============= standard library imports ========================
#============= local library imports  ==========================
from pychron.core.ui.combobox_editor import ComboboxEditor
from pychron.globals import globalv
from pychron.paths import paths


class LoginHandler(Handler):
    def closed(self, info, is_ok):
        if is_ok:
            info.object.dump()
        return True


def load_user_file():
    users = []
    path=paths.user_file
    if os.path.isfile(path):
        with open(path, 'r') as fp:
            users = pickle.load(fp)
    return users


def dump_user_file(names):
    users = load_user_file()
    if not isinstance(names, list):
        names=(names,)

    for name in names:
        if name not in users:
            users.append(name)

    with open(paths.user_file, 'w') as fp:
        pickle.dump(users, fp)


class Login(HasTraits):
    add_user_button = Button
    users = List
    ousers = List
    user = Str

    def dump(self):
        dump_user_file(self.user)

    def _add_user_button_fired(self):
        self.users = []

    def traits_view(self):
        v = View(Label('Select your username or enter a new one'),
                 HGroup(UItem('user', editor=ComboboxEditor(name='users'))),
                 handler=LoginHandler(),
                 buttons=['OK', 'Cancel'],
                 title='Login',
                 kind='livemodal')
        return v


def user_login():
    if globalv.use_login:
        #read the existing user file
        users = load_user_file()
        login = Login(users=users, ousers=users)
        while 1:
            info = login.edit_traits()
            if info.result:
                if login.user:
                    return login.user
            else:
                break
    else:
        return 'root'


#============= EOF =============================================



