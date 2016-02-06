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
from traits.api import List, Property, Str
from traitsui.api import View, VGroup, UItem
from traitsui.menu import Action
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.dvc.dvc_irradiationable import DVCAble


class OKButton(Action):
    name = 'OK'
    enabled_when = 'ok_enabled'
STYLESHEET = 'QLabel {font-size: 14px; color: red}'


class BaseEntry(DVCAble):

    value = Str
    available = List
    error_message = Str
    ok_enabled = Property(depends_on='value')
    tag = ''

    def do(self):
        return self._add_loop()

    def _get_ok_enabled(self):
        if self.value not in self.available:
            self.error_message = ''
            return True
        else:
            self.error_message = '{} already exists. Choose another'.format(self.tag)
            return False

    def _add_loop(self):
        while 1:
            info = self.edit_traits()
            if info.result:
                db = self.get_database()
                with db.session_ctx():
                    if self._add_item():
                        return True
            else:
                return False

    def _add_item(self):
        raise NotImplementedError

    def _new_view(self, *args, **kw):
        for a, v in (('buttons', ['OK', 'Cancel']),
                     ('resizable', True),
                     ('kind', 'livemodal')):
            if not kw.has_key(a):
                kw[a] = v

        v = View(*args, **kw)
        return v

    def traits_view(self):
        # style_sheet='QLabel {font-size: 10px} QLineEdit {font-size: 10px}'

        a = VGroup(UItem('value'),
                   UItem('error_message', style='readonly', style_sheet=STYLESHEET))
        buttons = [OKButton(), 'Cancel']
        return self._new_view(a,
                              width=400,
                              title='Add {}'.format(self.tag),
                              buttons=buttons)

# ============= EOF =============================================
