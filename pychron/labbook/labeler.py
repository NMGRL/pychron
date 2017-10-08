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

from traits.api import HasTraits, Str, Bool, Instance, List, Event

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.labbook.labels.label_adapter import LabelAdapter
from pychron.labbook.labels.views import NewLabelView
from pychron.loggable import Loggable
from pychron.paths import paths


class Label(HasTraits):
    text = Str
    color = Str
    active = Bool


class Path(HasTraits):
    relpath = Str
    labels = List

    @property
    def labels_strings(self):
        return [li.text for li in self.labels]


class Labeler(Loggable):
    db = Instance(LabelAdapter)
    labels = List
    selected = List(Label)
    dclick = Event
    label_event = Event
    refresh_needed = Event

    def __init__(self, *args, **kw):
        super(Labeler, self).__init__(*args, **kw)
        self._refresh_labels()

    def set_label(self, path, label):
        t = label.text
        if label.active:
            self.add_label_to_path(path, t)
        else:
            self.remove_label_from_path(path, t)

    def remove_label_from_path(self, path, label):
        self.info('removing label="{}" from path="{}"'.format(label, path))
        db = self.db
        dp = db.get_path(path)
        if dp:
            dl = db.get_label(label)
            if dl:
                dp.labels.remove(dl)

    def add_label_to_path(self, path, label):
        self.info('adding label="{}" to path="{}"'.format(label, path))
        db = self.db
        dp = db.get_path(path)
        if not dp:
            dp = db.add_path(path)
            db.flush()
        db.add_label_association(dp, label)

    def get_path(self, p):
        dp = self.db.get_path(p)
        if dp:
            return Path(relpath=dp.relpath, labels=[(Label(text=lb.text,
                                                           color=lb.color)) for lb in dp.labels])

    def new_label(self):
        v = NewLabelView()
        info = v.edit_traits()
        if info.result:
            self.add_label(v.text, v.color_str)
            self._refresh_labels()
            return True

    def add_label(self, text, color):
        self.db.add_label(text, color)

    def get_label(self, text):
        lb = self.db.get_label(text)
        if lb:
            return Label(text=lb.text, color=lb.color)

    def delete_label(self, text):
        self.db.delete_label(text)

    def load_labels_for_path(self, path):
        ls = []
        dp = self.db.get_path(path)
        if dp:
            labels = [li.text for li in dp.labels]
            ls = [Label(text=li.text, color=li.color) for li in dp.labels]
            for li in self.labels:
                li.active = li.text in labels

        self.selected = []
        self.refresh_needed = True
        return ls

    # handlers
    def _selected_changed(self):
        pass

    def _dclick_changed(self, new):
        if new:
            new.item.active = not new.item.active
            self.label_event = new.item
            self.selected = []
            self.refresh_needed = True

    # private
    def _refresh_labels(self):
        labels = self.db.get_labels()
        self.labels = [Label(text=li.text,
                             color=li.color,
                             cnt=li.cnt) for li in labels]

    def _db_default(self):
        path = os.path.join(paths.labbook_dir, 'labels.db')
        ldb = LabelAdapter(path=path)
        ldb.build_database()
        return ldb

# ============= EOF =============================================



