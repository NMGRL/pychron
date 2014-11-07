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
import hashlib
import os
from traits.api import HasTraits, Button, Str, Int, Bool, String, Property
from traitsui.api import View, Item, UItem, HGroup, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.tasks.base_editor import BaseTraitsEditor
from pychron.paths import paths


class NoteEditor(BaseTraitsEditor):
    note = String
    use_commit = Bool
    commit = String
    name = Property(depends_on='dirty, default_name')
    # _name = Str
    dirty = Bool
    # root = Str
    path = Str
    name_editable = Bool(True)
    ohash = Str
    default_name = Str

    def _get_name(self):
        if not self.path:
            name = self.default_name
        else:
            name = os.path.relpath(self.path, paths.labbook_dir)
        return name

    @property
    def commit_message(self):
        c = None
        if self.use_commit:
            c = self.commit

        if not c:
            c = 'modified' if os.path.isfile(self.path) else 'added'
            c = '{} {}'.format(c, self.name)
        return c

    def load(self, path=None):
        if path is None:
            path = self.path

        if not path or not os.path.isfile(path):
            return

        self.path = path
        # self.root, name = os.path.split(path)
        with open(path, 'r') as fp:
            note = fp.read()
            self.reset_hash(note)
            self.note = note
            self.name_editable = False

    def save(self, p):
        with open(p, 'w') as fp:
            fp.write(self.note)

        self.path = p
        self.reset_hash(self.note)

    def reset_hash(self, note):
        h = hashlib.sha1(note)
        self.ohash = h.hexdigest()
        self.dirty=False

    def _check_dirty(self):
        ch = hashlib.sha1(self.note)

        self.dirty = ch.hexdigest() != self.ohash

    def _note_changed(self):
        self._check_dirty()

    def traits_view(self):
        cgrp = VGroup(HGroup(Item('use_commit')),
                      UItem('commit', style='custom'))

        # v = View(VGroup(HGroup(Item('new_name', label='Name', visible_when='name_editable')),
        # VGroup(UItem('note', style='custom'),
        #                        cgrp)))
        v = View(VGroup(UItem('note', style='custom'),
                        cgrp))
        return v

# ============= EOF =============================================



