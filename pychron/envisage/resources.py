#===============================================================================
# Copyright 2014 Jake Ross
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
from pyface.image_resource import ImageResource

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.paths import paths

def icon(name):
    return ImageResource(name=name,search_path=paths.icon_search_path)

class Icon(ImageResource):
    def _search_path_default(self):
        print paths.icon_search_path
        return paths.icon_search_path
#============= EOF =============================================

