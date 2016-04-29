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
from pyface.file_dialog import FileDialog
from traits.api import HasTraits, List, Instance, Str
from traitsui.api import View, UItem, \
    VGroup, Handler, ListEditor
from traitsui.menu import Action

# ============= standard library imports ========================
import os
import yaml
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import get_path
from pychron.envisage.view_util import open_view
from pychron.experiment.conditional.groups import ConditionalGroup, ModificationGroup, ActionGroup, TruncationGroup, \
    CancelationGroup, TerminationGroup, EPostRunGroup, EPreRunGroup
from pychron.paths import paths
from pychron.experiment.conditional.conditional import ActionConditional, TruncationConditional, \
    CancelationConditional, TerminationConditional, QueueModificationConditional


class CEHandler(Handler):
    def object_path_changed(self, info):
        info.ui.title = '{} - [{}]'.format(info.object.title, info.object.name)

    def save_as(self, info):
        dlg = FileDialog(default_directory=paths.queue_conditionals_dir, action='save as')
        if dlg.open():
            if dlg.path:
                info.object.dump(dlg.path)


class ConditionalsViewable(HasTraits):
    group_names = ('actions', 'truncations', 'cancelations', 'terminations',
                   'post_run_terminations', 'pre_run_terminations', 'modifications')
    title = Str
    available_attrs = List
    groups = List
    selected_group = Instance(ConditionalGroup)
    help_str = Str

    def _selected_group_changed(self, new):
        if new:
            self.help_str = new.help_str

    def select_conditional(self, cond, tripped=False):
        tcond = type(cond)
        for gi in self.groups:
            for ci in gi.conditionals:
                if type(ci) is tcond:
                    # print '"{}" "{}", {}, {}'.format(ci, cond, id(ci), id(cond))
                    if ci == cond or ci.teststr == cond.teststr:
                        self.selected_group = gi
                        ci.tripped = tripped
                        return

    def _view_tabs(self):
        return UItem('groups', style='custom',
                     editor=ListEditor(use_notebook=True,
                                       style='custom',
                                       selected='selected_group',
                                       page_name='.label'))

    def _group_factory(self, items, klass, name=None, conditional_klass=None, label='', **kw):
        if conditional_klass is None:
            conditional_klass = TerminationConditional

        if name:
            items = items.get(name, []) if items else []

        group = klass(items, conditional_klass,
                      name=name,
                      label=label or name,
                      available_attrs=self.available_attrs)
        group.set_attrs(**kw)

        self.groups.append(group)
        return group


class ConditionalsEditView(ConditionalsViewable):
    path = Str
    root = Str
    detectors = List
    title = 'Edit Default Conditionals'

    # pre_run_terminations_group = Any

    def __init__(self, detectors=None, *args, **kw):
        attrs = ['', 'age', 'kca', 'kcl', 'cak', 'clk', 'rad40_percent',
                 'Ar40', 'Ar39', 'Ar38', 'Ar37', 'Ar36']

        ratio_matrix = ['Ar{}/Ar{}'.format(i, j) for i in ('40', '39', '38', '37', '36')
                        for j in ('40', '39', '38', '37', '36') if i != j]
        attrs.extend(ratio_matrix)
        if detectors:
            attrs.extend(detectors)
            self.detectors = detectors
        self.available_attrs = attrs
        super(ConditionalsEditView, self).__init__(*args, **kw)

    @property
    def name(self):
        v = ''
        if self.path:
            v = os.path.relpath(self.path, self.root)

        return v

    def open(self, path, save_as):
        self.load(path, save_as)

    def load(self, path, save_as):
        yd = None
        if path:
            root, name = os.path.split(path)
            p = get_path(root, name, ('.yaml', '.yml'))
            if p:
                if not save_as:
                    self.path = p

                with open(p, 'r') as rfile:
                    yd = yaml.load(rfile)

        if 'pre_run_terminations' in self.group_names:
            grp = self._group_factory(yd, EPreRunGroup, name='pre_run_terminations',
                                      label='PreRunTerminations',
                                      editable=True)
            grp.available_attrs = self.detectors

        for name, klass, cklass, label in (
                ('modifications', ModificationGroup, QueueModificationConditional, 'Modifications'),
                ('actions', ActionGroup, ActionConditional, 'Actions'),
                ('truncations', TruncationGroup, TruncationConditional, 'Truncations'),
                ('cancelations', CancelationGroup, CancelationConditional, 'Cancelations'),
                ('terminations', TerminationGroup, TerminationConditional, 'Terminations'),
                ('post_run_terminations', EPostRunGroup, TerminationConditional,
                 'PostRunTerminations')):
            if name in self.group_names:
                grp = self._group_factory(yd, klass, conditional_klass=cklass, name=name, label=label, editable=True)
                if name == 'post_run_terminations':
                    grp.available_attrs = self.detectors
                    # setattr(self, '{}_group'.format(name), grp)
                    # self.pre_run_terminations_group = grp

        self.selected_group = self.groups[0]

    def dump(self, path=None):
        if path is None:
            path = self.path
        else:
            self.path = path

        if not path:
            path = get_file_path(self.root, action='save as')

        if path:
            self.path = path
            with open(path, 'w') as wfile:
                # d = {k: getattr(self, '{}_group'.format(k)).dump() for k in self.group_names}
                d = {g.name: g.dump() for g in self.groups}
                yaml.dump(d, wfile, default_flow_style=False)

    def traits_view(self):
        v = View(VGroup(self._view_tabs(),
                        VGroup(UItem('help_str', style='readonly'),
                               label='Description',
                               show_border=True)),
                 width=1200,
                 resizable=True,
                 handler=CEHandler(),
                 buttons=['OK', 'Cancel', Action(name='Save As', action='save_as')],
                 title=self.title)

        return v


def get_file_path(root, action='open'):
    dlg = FileDialog(action=action,
                     wildcard=FileDialog.create_wildcard('YAML', '*.yaml *.yml'),
                     default_directory=root)
    if dlg.open():
        if dlg.path:
            return dlg.path


def edit_conditionals(name, detectors=None, app=None, root=None, save_as=False,
                      kinds=None, title=''):
    if not root:
        root = paths.queue_conditionals_dir

    if not save_as:
        if not name and not save_as:
            path = get_file_path(root)
            if not path:
                return
        else:
            path = os.path.join(root, name)
            #
            # if not os.path.isfile(path):
            # return
    else:
        path = ''

    cev = ConditionalsEditView(detectors, root=root, title=title)
    cev.open(path, save_as)
    if kinds:
        cev.group_names = kinds

    info = open_view(cev, kind='livemodal')

    if info.result:
        cev.dump()
        return cev.name


# ============= EOF =============================================
