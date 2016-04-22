# ===============================================================================
# Copyright 2013 Jake Ross
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
from pyface.constant import OK
from pyface.file_dialog import FileDialog
from traits.api import HasTraits, Float, Enum, List, Int, \
    File, Property, Button, on_trait_change, Any, Event, cached_property
from traits.trait_errors import TraitError
from traitsui.api import View, UItem, HGroup, Item, spring, EnumEditor, VGroup
from traitsui.tabular_adapter import TabularAdapter

# ============= standard library imports ========================
import csv
import os
from hashlib import sha256
# ============= local library imports  ==========================
from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.paths import paths
from pychron.viewable import Viewable
from pychron.pychron_constants import alphas


# paths.build('_experiment')
# build_directories(paths)


class BaseIncrementalHeatAdapter(TabularAdapter):
    columns = [('Step', 'step_id'),
               ('Value', 'value'),
               ('Units', 'units'),
               ('Duration (s)', 'duration'),
               ('Cleanup (s)', 'cleanup')]

    step_id_width = Int(40)
    step_id_text = Property
    units_text = Property

    def _get_units_text(self):
        return self.item.units

    def _set_units_text(self, v):
        try:
            self.item.units = v
        except TraitError:
            pass

    def _get_step_id_text(self):
        return alphas(self.item.step_id - 1)


class LaserIncrementalHeatAdapter(BaseIncrementalHeatAdapter):
    columns = [('Step', 'step_id'),
               ('Value', 'value'),
               ('Units', 'units'),
               ('Duration (s)', 'duration'),
               ('Cleanup (s)', 'cleanup'),
               ('Beam Diameter', 'beam_diameter')]

    beam_diameter_text = Property

    def _get_beam_diameter_text(self):
        bd = self.item.beam_diameter
        if bd is None:
            bd = ''
        return bd


class BaseIncrementalHeatStep(HasTraits):
    step_id = Int
    duration = Float
    cleanup = Float
    value = Float
    units = Enum('watts', 'temp', 'percent')

    #    is_ok = Property
    step = Property(depends_on='step_id')

    @cached_property
    def _get_step(self):
        return alphas(self.step_id - 1)

    def make_row(self):
        return self.value, self.units, self.duration, self.cleanup

    def make_dict(self, gdur, gcleanup):
        dur = self.duration
        if not dur:
            dur = gdur

        cleanup = self.cleanup
        if not cleanup:
            cleanup = gcleanup

        d = dict(extract_value=self.value,
                 extract_units=self.units,
                 duration=dur,
                 cleanup=cleanup)

        return d

    def to_string(self):
        return ','.join(map(str, self.make_row()))

    @property
    def is_valid(self):
        return self.value and self.duration


class LaserIncrementalHeatStep(BaseIncrementalHeatStep):
    beam_diameter = Property(depends_on='_beam_diameter')
    _beam_diameter = Float(default_value=None)

    def make_dict(self, gdur, gcleanup):
        d = super(LaserIncrementalHeatStep, self).make_dict(gdur, gcleanup)
        if self.beam_diameter is not None:
            d['beam_diameter'] = self.beam_diameter
        return d

    def make_row(self):
        return self.value, self.units, self.duration, \
               self.cleanup, self.beam_diameter if self.beam_diameter is not None else ''

    def _get_beam_diameter(self):
        return self._beam_diameter

    def _set_beam_diameter(self, v):
        self._beam_diameter = v


class BaseIncrementalHeatTemplate(Viewable):
    steps = List
    step_klass = BaseIncrementalHeatStep
    adapter_klass = BaseIncrementalHeatAdapter

    name = Property(depends_on='path')
    path = File
    names = List

    save_button = Button('save')
    save_as_button = Button('save as')
    add_row = Button('add step')
    title = Property

    selected = Any
    refresh_needed = Event

    units = Enum('', 'watts', 'temp', 'percent')

    gduration = Float
    gcleanup = Float

    # ===============================================================================
    # persistence
    # ===============================================================================
    def load(self, path):

        self.path = path
        self.steps = []
        with open(path, 'r') as rfile:
            reader = csv.reader(rfile)
            header = reader.next()
            cnt = 1
            for row in reader:
                if row:
                    params = self._parse_row(row, header)

                    step = self.step_klass(step_id=cnt,
                                           **params)
                    self.steps.append(step)
                    cnt += 1

    def dump(self, path):
        with open(path, 'w') as wfile:
            writer = csv.writer(wfile)
            header = ('value', 'units', 'duration', 'cleanup', 'beam_diameter')
            writer.writerow(header)
            for step in self.steps:
                writer.writerow(step.make_row())

    # private
    def _parse_row(self, row, header):
        params = dict()
        for a, cast in (('value', float), ('units', str),
                        ('duration', float), ('cleanup', float)):
            idx = header.index(a)
            params[a] = cast(row[idx])
        return params

    def _gduration_changed(self):
        self._set_steps_attr('duration', self.gduration)

    def _gcleanup_changed(self):
        self._set_steps_attr('cleanup', self.gcleanup)

    def _units_changed(self):
        self._set_steps_attr('units', self.units)

    def _set_steps_attr(self, attr, v):
        steps = self.selected
        if not steps:
            steps = [s for s in self.steps if s.value]

        for si in steps:
            setattr(si, attr, v)
        self.refresh_needed = True

    def _get_title(self):
        if self.path:
            return os.path.basename(self.path)
        else:
            return ' '

    def _steps_default(self):
        return [self.step_klass(step_id=i + 1) for i in range(20)]

    def _get_name(self):
        return os.path.basename(self.path)

    def _set_name(self, v):
        self.load(os.path.join(paths.incremental_heat_template_dir, v))

    # def _calculate_similarity(self, template2):
    #     with open(self.path, 'r') as rfile:
    #         s1 = rfile.read()
    #
    #     with open(template2.path, 'r') as rfile:
    #         s2 = rfile.read()
    #
    #     e = 0
    #     s1s = [l for l in s1.splitlines() if l.split(',')!=0.0]
    #     s2s = [l for l in s1.splitlines() if l.split(',')!=0.0]
    #
    #     if len
    #     diff = ndiff(s1.splitlines(), s2.splitlines(), linejunk=lambda x: x.sp)
    #     for line in diff:
    #         if line[0] == '?':
    #             e += 1
    #
    #         print line
    #     print e
    #     return e
    #
    # def _check_similarity(self):
    #     sims = []
    #     temps = list_directory(paths.incremental_heat_template_dir, extension='.txt')
    #     for ti in temps:
    #         if ti == self.name:
    #             continue
    #
    #         t = self.__class__()
    #         p = os.path.join(paths.incremental_heat_template_dir, ti)
    #         try:
    #             t.load(p)
    #         except BaseException:
    #             self.debug('invalid template {}. removing this file'.format(p))
    #             os.remove(p)
    #             continue
    #
    #         e = self._calculate_similarity(t)
    #         if e < 10:
    #             sims.append(ti)
    #     return sims

    def _generate_name(self):
        # get active steps
        steps = [s for s in self.steps if s.is_valid]
        n = len(steps)
        first, last = steps[0], steps[-1]

        h = sha256()
        attrs = ('step_id', 'duration', 'cleanup', 'value', 'beam_diameter')
        for s in steps:
            for a in attrs:
                if hasattr(s, a):
                    h.update(str(getattr(s, a)))

        d = h.hexdigest()
        return '{}Step{}-{}_{}.txt'.format(n, first.value, last.value, d[:8])

    # ===============================================================================
    # handlers
    # ===============================================================================
    @on_trait_change('steps[]')
    def _steps_updated(self):
        for i, si in enumerate(self.steps):
            si.step_id = i + 1

    def _add_row_fired(self):
        if self.selected:
            for si in self.selected:
                step = si.clone_traits()
                self.steps.append(step)
        else:
            if self.steps:
                step = self.steps[-1].clone_traits()
            else:
                step = self.step_klass()

            self.steps.append(step)

    def _save_button_fired(self):
        # sims = self._check_similarity()
        # if sims:
        #     if not self.confirmation_dialog('Similar templates already exist. \n{}\n'
        #                                     'Are you sure you want to save this template?'.format('\n'.join(sims))):
        #         return

        self.dump(self.path)
        self.close_ui()

    def _save_as_button_fired(self):
        # sims = self._check_similarity()
        # if sims:
        #     if not self.confirmation_dialog('Similar templates already exist. {}\n '
        #                                     'Are you sure you want to save this template?'.format(','.join(sims))):
        #         return

        default_filename = self._generate_name()

        dlg = FileDialog(action='save as',
                         default_filename=default_filename,
                         default_directory=paths.incremental_heat_template_dir)
        if dlg.open() == OK:
            path = dlg.path
            if not path.endswith('.txt'):
                path = '{}.txt'.format(path)

            self.dump(path)
            self.path = path
            self.close_ui()

    def traits_view(self):
        editor = myTabularEditor(adapter=self.adapter_klass(),
                                 refresh='refresh_needed',
                                 selected='selected',
                                 # copy_cache='copy_cache',
                                 # pasted='pasted',
                                 multi_select=True)

        # cols=[ObjectColumn(name='step', label='Step', editable=False),
        #       ObjectColumn(name='value',label='Value'),
        #       ObjectColumn(name='units',label='Units'),
        #       ObjectColumn(name='duration', label='Duration (S)'),
        #       ObjectColumn(name='cleanup', label='Cleanup (S)')]
        #
        # editor=TableEditor(columns=cols, selected='selected',
        #                    deletable=True,
        #                    show_toolbar=True,
        #                    selection_mode='rows', sortable=False)

        v = View(VGroup(HGroup(UItem('name', editor=EnumEditor(name='names')),
                               icon_button_editor('add_row', 'table_add'), spring,
                               Item('gduration', label='Duration'),
                               Item('gcleanup', label='Cleanup'),
                               Item('units')),
                        UItem('steps',
                              style='custom',
                              editor=editor),

                        HGroup(UItem('save_button', enabled_when='path'),
                               UItem('save_as_button'))),
                 height=500,
                 width=900,
                 resizable=True,
                 title=self.title,
                 handler=self.handler_klass)
        return v


class LaserIncrementalHeatTemplate(BaseIncrementalHeatTemplate):
    step_klass = LaserIncrementalHeatStep
    adapter_klass = LaserIncrementalHeatAdapter

    def _parse_row(self, row, header):
        params = super(LaserIncrementalHeatTemplate, self)._parse_row(row, header)
        try:
            idx = header.index('beam_diameter')
        except ValueError:
            idx = None

        if idx is not None:
            v = row[idx]
            if v.strip():
                try:
                    params['beam_diameter'] = float(v)
                except ValueError:
                    self.warning('Invalid beam_diameter value {}'.format(v))
        return params


if __name__ == '__main__':
    paths.build('_dev')
    im = LaserIncrementalHeatTemplate()
    im.load(os.path.join(paths.incremental_heat_template_dir,
                         'a.txt'
                         ))

    #    for i in range(10):
    #        im.steps.append(IncrementalHeatStep(step_id=i + 1))
    im.configure_traits()
# ============= EOF =============================================
