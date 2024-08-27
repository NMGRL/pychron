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
from __future__ import absolute_import

from pyface.message_dialog import information
from traits.trait_types import List

from pychron.core.ui import set_qt
from pychron.core.yaml import yload

# set_qt()
# ============= enthought library imports =======================
import os
from traits.api import HasTraits, Str

# ============= standard library imports ========================
# ============= local library imports  ==========================
import yaml
from pychron.paths import paths


# from pychron.core.ui.keybinding_editor import KeyBindingEditor

# default_key_map = {'pychron.open_experiment': ('O', 'Open Experiment'),
# 'pychron.new_experiment': ('N', 'New Experiment'),
# 'pychron.deselect': ('Ctrl+Shift+D', 'Deselect'),
# 'pychron.open_last_experiment': ('Alt+Ctrl+O', 'Open Last Experiment')}


def key_bindings_path():
    return os.path.join(paths.appdata_dir, "key_bindings")
    # return os.path.join(paths.hidden_dir, 'key_bindings.{}'.format(globalv.username))


def load_key_map():
    p = key_bindings_path()
    if os.path.isfile(p):
        return yload(p)
    else:
        return {}


user_key_map = load_key_map()


def update_key_bindings(actions):
    if isinstance(user_key_map, dict):
        for aid, b, d in actions:
            if aid not in user_key_map:
                user_key_map[aid] = (b, d)

        dump_key_bindings(user_key_map)
    else:
        # corrupted keybindings file. writing an empty one
        dump_key_bindings({})


def dump_key_bindings(obj):
    p = key_bindings_path()
    with open(p, "w") as wfile:
        yaml.dump(obj, wfile)


def keybinding_exists(key):
    for k, (b, d) in user_key_map.items():
        if b == key:
            return d


def clear_keybinding(desc):
    for k, (b, d) in user_key_map.items():
        if d == desc:
            user_key_map[k] = ("", d)
            dump_key_bindings(user_key_map)
            return


class mKeyBinding(HasTraits):
    binding = Str
    description = Str
    # refresh_needed = Event
    # dump_needed = Event
    id = Str

    # def _refresh_needed_fired(self):
    #     print 'asdfasdasdfsafd'


class mKeyBindings(HasTraits):
    bindings = List(mKeyBinding)

    # @on_trait_change('bindings:dump_needed')
    def dump(self):
        return {bi.id: (bi.binding, bi.description) for bi in self.bindings}
        #
        #
        # @on_trait_change('bindings:refresh_needed')
        # def handle(self):
        #     # for k, v in user_key_map.iteritems():
        #     #     print k, v
        #     km = load_key_map()
        #     bs = [mKeyBinding(binding=v[0], description=v[1], id=k) for k, v in km.items()]
        #     self.bindings = bs


def edit_key_bindings():
    from pychron.core.ui.qt.keybinding_editor import KeyBindingsEditor

    ks = [
        mKeyBinding(id=k, binding=v[0], description=v[1])
        for k, v in user_key_map.items()
    ]
    kb = mKeyBindings(bindings=ks)
    # kb.handle()

    ed = KeyBindingsEditor(model=kb)
    info = ed.edit_traits()
    if info.result:
        dump_key_bindings(kb.dump())
        information(None, "Changes take effect on Restart")
        # ed.edit_traits()
        # kb.edit_traits()


if __name__ == "__main__":
    edit_key_bindings()
# ============= EOF =============================================
