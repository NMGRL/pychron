# ===============================================================================
# Copyright 2015 Jake Ross
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
# from traitsui.editors import ButtonEditor
from traitsui.item import Item

from pychron.core.helpers.filetools import add_extension
from pychron.core.ui.button_editor import ButtonEditor
from pychron.envisage.resources import icon


def icon_button_editor(trait, name, label=None, editor_kw=None, **kw):
    if editor_kw is None:
        editor_kw = {}

    name = add_extension(name, '.png')
    # name = '{}.png'.format(name)
    kw['show_label'] = label is not None
    kw['label'] = label or ''
    image = icon(name)

    return Item(trait, style='custom', editor=ButtonEditor(image=image, **editor_kw), **kw)

# ============= EOF =============================================
