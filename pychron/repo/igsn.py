# ===============================================================================
# Copyright 2013 Jake Ross
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
# ===============================================================================

# ============= enthought library imports =======================
from traits.api import Str, Button, Event

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.ui.preference_binding import bind_preference
from pychron.repo.http_repository import HTTPRepository


class IGSNRepository(HTTPRepository):
    # url = Str('http://matisse.kgs.ku.edu/geochronid')
    # url = Str('http://localhost:8080')
    usercode = Str

    get_igsn_button = Button('Get IGSN')

    project = Str
    sample = Str
    parent_igsn = Str

    # display_str = Property(depends_on='sample, project')
    new_igsn = Event

    def __init__(self, *args, **kw):
        super(IGSNRepository, self).__init__(*args, **kw)
        self._bind_preferences()

    def _bind_preferences(self):
        prefid = 'pychron.igsn'
        bind_preference(self, 'url', '{}.url'.format(prefid))
        bind_preference(self, 'username', '{}.username'.format(prefid))
        bind_preference(self, 'password', '{}.password'.format(prefid))
        bind_preference(self, 'usercode', '{}.usercode'.format(prefid))

    # @on_trait_change('sample, username, password')
    # def _update_enabled(self):
    #     self.enabled = all([getattr(self, a)
    #                              for a in ('sample', 'username', 'password')])
    #
    # def _get_display_str(self):
    #     return '{} {}'.format(self.project, self.sample)
    #
    # def _get_igsn_button_fired(self):
    #     self.debug('get igsn fired')
    #     self.get_igsn()

    def get_igsn(self):
        form = self._new_form()
        form['GeoObject Type'] = 'individual sample'
        if self.parent_igsn:
            form['Parent GeochronID'] = self.parent_igsn

        self.post('', form)

    def _handle_post(self, resp):
        """
            parse resp

            the new igsn should be in the response
        """
        new_igsn = 'foodat'
        self.new_igsn = new_igsn
# ============= EOF =============================================
