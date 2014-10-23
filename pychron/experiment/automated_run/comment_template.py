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
from traits.api import List, Dict
# ============= standard library imports ========================
#============= local library imports  ==========================
from pychron.core.templater.base_templater import BaseTemplater


class CommentTemplater(BaseTemplater):
    attributes = List(['irrad_level', 'irrad_hole', '<SPACE>'])
    example_context = Dict({'irrad_level': 'A',
                            'irrad_hole': '9'})

    base_predefined_labels = List(['', 'irrad_level : irrad_hole'])

    label = 'irrad_level : irrad_hole'
    persistence_name = 'comment'

    width = 600
    view_title = 'Edit Comment Template'

    def render(self, obj):
        f = self.formatter
        return f.format(**self._generate_context(obj))

    def _generate_context(self, obj):
        ctx = {}
        for ai in self.attributes:
            ctx[ai] = getattr(obj, ai)
        return ctx


if __name__ == '__main__':
    c = CommentTemplater()
    c.configure_traits()

#============= EOF =============================================



