#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import Str, Bool
from pychron.core.xml.xml_parser import XMLParser
from pychron.processing.repository.http_repository import HTTPRepository
#============= standard library imports ========================
#============= local library imports  ==========================


class GeochronRepository(HTTPRepository):

    is_public = Bool
    overwrite = Bool
#     upload = Str('http://www.geochronportal.org/')
#     upload_url = Str('uploadservice.php')
    url = Str('http://localhost')
    upload_url = Str('foo.php')

    def upload(self):
        '''
            use an http POST to upload data
        '''

#         form = dict()
        content = self._assemble_xml()
        if content:
            form = self._new_form()
            form['content'] = content
            form['public'] = 'yes' if self.is_public else 'no'
            form['overwrite'] = 'yes' if self.overwrite else 'no'

            self.post(self.upload_url, form)

    def _handle_post(self, resp):
        pass


    def _assemble_xml(self):
        return 'asfafasfafsd'
        xp = XMLParser()
        return xp.tostring()

if __name__ == '__main__':
    g = GeochronRepository()
    g.upload()
#============= EOF =============================================
