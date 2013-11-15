#===============================================================================
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
from traits.api import HasTraits, Str, Password, on_trait_change, Any, \
    Button
from traitsui.api import View, Item, spring, HGroup
#============= standard library imports ========================
import hashlib
import uuid
#============= local library imports  ==========================
from pychron.ui.custom_label_editor import CustomLabel
from pychron.loggable import Loggable
class NewAccount(HasTraits):
    username = Str
    password = Password
    password2 = Password
    message = Str('Enter a username and password')
    def traits_view(self):
        v = View(
                 CustomLabel('message'),
                 Item('username'),
                 Item('password'),
                 Item('password2', label='Password'),
                 kind='modal',
                 buttons=['OK', 'Cancel'],
                 title='New Account'
               )
        return v

class Credentials(Loggable):
    username = Str
    password = Password
    message = Str('Enter your username and password')
    db = Any

    create_account = Button('Create Account')
    def _create_account_fired(self):
        nc = NewAccount()
        info = nc.edit_traits()
        if info.result:
            if nc.password != nc.password2:
                self.warning_dialog('Passwords did not match')
            else:
                if self.db.connect(force=True):
                    if self.db.get_user(nc.username):
                        self.warning_dialog('User {} already exists'.format(nc.username))
                    else:
                        password, salt = self.generate_hashed_password(nc.password)
                        self.db.add_user(nc.username, password=password, salt=salt)
                        self.db.commit()

    def verify(self, stored_password, salt, use_hex=True):
        hh, _salt = self.generate_hashed_password(self.password, salt, use_hex)
        self.debug('generated       hash: {}'.format(hh))
        self.debug('stored_password  pwd: {}'.format(stored_password))
        return hh == stored_password

    @classmethod
    def generate_hashed_password(cls, password, salt=None, use_hex=True):

        if use_hex:
            attr = 'hex'
            func = 'hexdigest'
        else:
            attr = 'bytes'
            func = 'digest'

        if salt is None:
            salt = getattr(uuid.uuid4(), attr)

        hh = hashlib.sha512(password + salt)
        return getattr(hh, func)(), salt

    def traits_view(self):
        v = View(
                 CustomLabel('message'),
                 Item('username'),
                 Item('password'),
                 HGroup(spring, Item('create_account',
                                     enabled_when='db',
                                     show_label=False)),
                 kind='modal',
                 buttons=['OK', 'Cancel'],
                 title='Credentials'
               )
        return v



#============= EOF =============================================
