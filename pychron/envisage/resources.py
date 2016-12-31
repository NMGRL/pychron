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

from pyface.image_resource import ImageResource

from pychron.core.helpers.filetools import add_extension
from pychron.paths import paths, icon_search_path, splashes


def image(name):
    name = add_extension(name, '.png')
    for si in paths.image_search_path:
        if si and os.path.isfile(os.path.join(si, name)):
            break
    else:
        print 'no image for "{}"'.format(name)

    return ImageResource(name=name, search_path=paths.image_search_path)


def icon(name):
    name = add_extension(name, '.png')
    if icon_search_path:
        for si in icon_search_path:
            if si and os.path.isfile(os.path.join(si, name)):
                break
        else:
            print 'no icon for "{}"'.format(name)
    return ImageResource(name=name, search_path=icon_search_path)


def splash_icon(appname):
    name = 'splash.png'
    ps = icon_search_path
    for si in icon_search_path:
        if si and os.path.isfile(os.path.join(si, name)):
            print 'found splash', os.path.isfile(os.path.join(si, name))
            break
    else:
        if appname:
            name = 'splash_{}.png'.format(appname)
            ps.append(splashes)

    return ImageResource(name=name, search_path=ps)


class Icon(ImageResource):
    def _search_path_default(self):
        return icon_search_path

# ============= EOF =============================================

