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
from traits.api import HasTraits, Button, Str, Int, Bool
from traitsui.api import View, Item, UItem, HGroup, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.key_bindings import KeyBindings, KeyBinding
import yaml
from pychron.globals import globalv
from pychron.paths import paths

# default_key_map = {'pychron.open_experiment': ('O', 'Open Experiment'),
#                    'pychron.new_experiment': ('N', 'New Experiment'),
#                    'pychron.deselect': ('Ctrl+Shift+D', 'Deselect'),
#                    'pychron.open_last_experiment': ('Alt+Ctrl+O', 'Open Last Experiment')}


def key_bindings_path():
    return os.path.join(paths.hidden_dir, 'key_bindings.{}'.format(globalv.username))


def load_key_map():
    p = key_bindings_path()
    # if not os.path.isfile(p):
        # dump_key_bindings(default_key_map)
    if os.path.isfile(p):
        with open(p, 'r') as fp:
            return yaml.load(fp)
    else:
        return {}


user_key_map = load_key_map()

def update_key_bindings(actions):
    for aid, b, d in actions:
        if not aid in user_key_map:
            user_key_map[aid] = (b, d)

    dump_key_bindings(user_key_map)


def dump_key_bindings(obj):
    p = key_bindings_path()
    with open(p, 'w') as fp:
        yaml.dump(obj, fp)


def edit_key_bindings():
    pass
    # ks=[KeyBinding(binding1=v[0], description=v[1]) for k,v in user_key_map.items()]
    # kb=KeyBindings(*ks)
    # kb.edit_traits()


# ============= EOF =============================================



