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
from traits.has_traits import HasTraits
from traits.trait_types import Button, List, String, Any, Str, Dict
from traits.traits import Property
from traitsui.editors import EnumEditor, ListStrEditor
from traitsui.group import VGroup, HGroup
from traitsui.item import Item, UItem
from traitsui.view import View
#============= standard library imports ========================
import os
import pickle
#============= local library imports  ==========================
from pychron.envisage.tasks.pane_helpers import icon_button_editor
from pychron.paths import paths


class BaseTemplater(HasTraits):
    formatter = Property(depends_on='label')
    clear_button = Button
    keywords = List
    non_keywords = List
    label = String
    activated = Any
    example = Property(depends_on='label')
    view_title = Str

    predefined_label = Str
    predefined_labels = Property(depends_on='user_predefined_labels')
    base_predefined_labels = List([''])
    user_predefined_labels = List

    add_enabled = Property(depends_on='label')
    delete_enabled = Property(depends_on='label')
    add_label_button = Button
    delete_label_button = Button

    attribute_keys = Property(depends_on='label')

    width = 0.0
    persistence_name = ''

    attributes = List
    example_context = Dict
    attribute_formats = Dict

    def __init__(self, *args, **kw):
        super(BaseTemplater, self).__init__(*args, **kw)
        self.load()

    #persistence
    def load(self):
        p = os.path.join(paths.hidden_dir, self.persistence_name)
        if os.path.isfile(p):
            with open(p, 'r') as fp:
                try:
                    self.user_predefined_labels = pickle.load(fp)
                except BaseException:
                    pass

    def dump(self):
        p = os.path.join(paths.hidden_dir, self.persistence_name)
        with open(p, 'w') as fp:
            try:
                pickle.dump(self.user_predefined_labels, fp)
            except BaseException:
                pass

    def _get_attribute_keys(self):
        ks = []
        for k in self.label.split(' '):
            if k in self.attributes:
                ks.append(k.lower())

        return ks

    def _get_formatter(self):
        ns = []
        for k in self.label.split(' '):
            if k in self.attributes:
                if k == '<SPACE>':
                    k = ' '
                else:
                    k = k.lower()
                    try:
                        f = self.attribute_formats[k]
                    except KeyError:
                        f='s'

                    k = '{{{}:{}}}'.format(k, f)
            ns.append(k)
        s = ''.join(ns)
        return s

    def _get_example(self):
        f = self.formatter
        return f.format(**self.example_context)

    def _get_predefined_labels(self):
        return self.base_predefined_labels + self.user_predefined_labels

    def _get_add_enabled(self):
        return self.label and self.label not in self.predefined_labels

    def _get_delete_enabled(self):
        return self.label in self.user_predefined_labels

    def _delete_label_button_fired(self):
        if self.label in self.user_predefined_labels:
            self.user_predefined_labels.remove(self.label)
            self.dump()
            self.load()
            self.label = ''

    #handlers
    def _add_label_button_fired(self):
        if self.label not in self.predefined_labels:
            self.user_predefined_labels.append(self.label)
            self.dump()
            self.load()

    def _clear_button_fired(self):
        self.label = ''
        self.predefined_label = ''

    def _activated_changed(self, new):
        if new:
            self.keywords.append(new)
            if self.label:
                self.label += ' {}'.format(new)
            else:
                self.label = new

            self.activated = None

    def _predefined_label_changed(self, new):
        self.label = new

    #views
    def _get_main_view(self):
        return VGroup(HGroup(Item('predefined_label',
                                  editor=EnumEditor(name='predefined_labels'))),
                      UItem('attributes',
                            editor=ListStrEditor(
                                editable=False,
                                activated='activated')),
                      HGroup(UItem('label'),
                             icon_button_editor('clear_button', 'clear',
                                                tooltip='Clear current label'),
                             icon_button_editor('add_label_button', 'add',
                                                enabled_when='add_enabled',
                                                tooltip='Save current label to the predefined list'),
                             icon_button_editor('delete_label_button', 'delete',
                                                enabled_when='delete_enabled',
                                                tooltip='Remove current label from the predefined list'),
                             label='Label',
                             show_border=True),
                      HGroup(UItem('example', style='readonly'), label='Example',
                             show_border=True))

    def _get_additional_groups(self):
        pass

    def traits_view(self):
        vg = VGroup(self._get_main_view())
        grps = self._get_additional_groups()
        if grps:
            vg.content.extend(grps)

        v = View(
            vg,
            resizable=True,
            width=self.width,
            title=self.view_title,
            buttons=['OK', 'Cancel'],
            kind='livemodal')
        return v
#============= EOF =============================================
