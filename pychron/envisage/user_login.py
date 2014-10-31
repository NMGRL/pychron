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
from traitsui.api import View, Item, HGroup, UItem, Label, Handler, VGroup
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
    path=paths.users_file
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

    with open(paths.users_file, 'w') as fp:
        pickle.dump(users, fp)


class Login(HasTraits):
    users = List
    user = Str

    def dump(self):
        dump_user_file(self.user)


    def traits_view(self):
        v = View(Label('Select your username or enter a new one'),
                 HGroup(UItem('user', editor=ComboboxEditor(name='users'))),
                 handler=LoginHandler(),
                 buttons=['OK', 'Cancel'],
                 title='Login',
                 kind='livemodal')
        return v


class SrcDestUsers(HasTraits):
    users=List
    src_user =Str
    dest_user =Str

    def traits_view(self):
        v = View(Label('Copy "Source" preferences to "Destination"'),
                 VGroup(UItem('src_user', editor=ComboboxEditor(name='users')),
                        label='Source', show_border=True),
                 VGroup(UItem('dest_user', editor=ComboboxEditor(name='users')),
                        label='Destination', show_border=True),
                 buttons=['OK', 'Cancel'],
                 title='Login',
                 kind='livemodal')
        return v


def get_user(current=None):
    if globalv.use_login:
        #check to see if the login file is set
        if os.path.isfile(paths.login_file):
            with open(paths.login_file, 'r') as fp:
                u=fp.read()
            os.remove(paths.login_file)
            return u

        #read the existing user file
        users = load_user_file()
        if current:
            users =[u for u in users if u!=current]

        login = Login(users=users)
        if users:
            login.user = users[0]
        while 1:
            info = login.edit_traits()
            if info.result:
                if login.user:
                    return login.user
            else:
                break
    else:
        return 'root'


def get_src_dest_user(cuser):
    users = load_user_file()
    login = SrcDestUsers(users=users)
    login.src_user=cuser
    s,d=None, None
    while 1:
        info = login.edit_traits()
        if info.result:
            if login.src_user and login.dest_user:
                s,d =login.src_user,login.dest_user
                break
        else:
            break

    return s,d
#============= EOF =============================================



