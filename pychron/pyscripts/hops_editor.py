#===============================================================================
# Copyright 2014 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#===============================================================================
from pychron.core.ui import set_qt
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.paths import paths

set_qt()

#============= enthought library imports =======================
from traitsui.handler import Controller
from traitsui.table_column import ObjectColumn
from pyface.constant import OK
from pyface.file_dialog import FileDialog
from traits.api import HasTraits, Str, List, Int, Any, Button, Bool
from traitsui.menu import ToolBar, Action
from traitsui.api import View, Item, UItem, HGroup, InstanceEditor, HSplit, VGroup, EnumEditor

#============= standard library imports ========================
import os
#============= local library imports  ==========================
from pychron.envisage.resources import icon
from pychron.core.helpers.filetools import fileiter, add_extension
from pychron.experiment.automated_run.hop_util import split_hopstr
from pychron.loggable import Loggable
from pychron.envisage.tasks.pane_helpers import icon_button_editor
from pychron.core.ui.table_editor import myTableEditor

# class NullInt(Int):
#     default_value = None

class Position(HasTraits):
    detector = Str
    isotope = Str
    deflection = Int
    name = Str
    # available_isotopes=Property(depends_on='isotope')
    #
    # def _get_available_isotopes(self):
    #     from pychron.pychron_constants import ISOTOPES
    #     isos=list(ISOTOPES)
    #     isos.remove(self.isotope)
    #     return isos

    def to_string(self):
        s = '{}:{}'.format(self.isotope, self.detector)
        if self.deflection:
            s = '{}:{}'.format(s, self.deflection)
        return s


class Hop(HasTraits):
    positions = List
    counts = Int
    settle = Int
    name = Str
    detectors = List(['A, B'])
    add_position_button = Button
    remove_position_button = Button
    selected = Any
    error_message = Str

    def to_string(self):
        vs = [str(self.counts), str(self.settle)]
        hs = "'{}'".format(', '.join([p.to_string() for p in self.positions
                                      if p.isotope and p.detector]))

        return '({}, {})'.format(hs, ', '.join(vs))

    def parse_hopstr(self, hs):
        for is_baseline, iso, det, defl in split_hopstr(hs):
            p = Position(isotope=iso,
                         detector=det,
                         deflection=int(defl) if defl else 0)
            self.positions.append(p)

    def validate_hop(self):
        """
            return true if no duplicates
        """
        self.error_message = ''
        n = len(self.positions)
        ps = {p.isotope for p in self.positions}
        dup_iso = len(set(ps)) < n
        if dup_iso:
            self.error_message = self._make_error_message('isotope')

        ds = {p.detector for p in self.positions}
        dup_det = len(ds) < n
        if dup_det:
            em = self._make_error_message('detector')
            if self.error_message:
                self.error_message = '{}; {}'.format(self.error_message, em)
            else:
                self.error_message = em

        return not (dup_iso or dup_det)

    def _make_error_message(self, attr):
        dets = []
        ps = []
        for p in self.positions:
            det = getattr(p, attr)
            if det in dets:
                ps.append(det)
            dets.append(det)
        return 'Multiple {}s: {}'.format(attr.capitalize(), ', '.join(ps))

    def _add_position_button_fired(self):
        self.positions.append(Position())

    def _remove_position_button_fired(self):
        self.positions.remove(self.selected)

    def traits_view(self):
        from pychron.pychron_constants import ISOTOPES

        cols = [
            ObjectColumn(name='name', label='', editable=False),
            ObjectColumn(name='isotope',
                         editor=EnumEditor(values=ISOTOPES)),
            ObjectColumn(name='detector',
                         editor=EnumEditor(values=self.detectors)),
            ObjectColumn(name='deflection', )]

        v = View(VGroup(HGroup(Item('counts',
                                    tooltip='Number of measurements at this position'),
                               Item('settle', label='Settle (s)',
                                    tooltip='Delay in seconds after magnet move and before measurement')),
                        UItem('positions',
                              editor=myTableEditor(columns=cols,
                                                   sortable=False,
                                                   clear_selection_on_dclicked=True,
                                                   selected='selected')),
                        HGroup(icon_button_editor('add_position_button', 'add',
                                                  tooltip='Add isotope/detector to measure'),
                               icon_button_editor('remove_position_button', 'delete',
                                                  tooltip='Remove selected isotope/detector',
                                                  enabled_when='selected'))))
        return v


class HopSequence(HasTraits):
    hops = List

    def to_string(self):
        return '\n'.join([hi.to_string() for hi in self.hops])

    def add_hop(self, idx):
        if idx is not None:
            h = self.hops[idx]
            hh = h.clone_traits()
            self.hops.insert(idx, hh)
        else:
            h = Hop()
            self.hops.append(h)

        self._label_hops()

    def _label_hops(self):
        for i, hi in enumerate(self.hops):
            hi.name = str(i + 1)

    def remove_hop(self, idx):
        self.hops.pop(idx)
        self._label_hops()


class HopEditorModel(Loggable):
    hop_sequence = HopSequence
    selected = Any
    path = Str
    detectors = List
    add_hop_button = Button
    remove_hop_button = Button
    saveable = Bool
    saveasable = Bool

    def new(self):
        self.hop_sequence = HopSequence()

    def open(self):
        p = '/Users/ross/Pychrondata_dev/scripts/measurement/hops/hop.txt'
        if not os.path.isfile(p):
            p = ''
            dialog = FileDialog(action='open', default_directory=paths.hops_dir)
            if dialog.open() == OK:
                p = dialog.path

        if os.path.isfile(p):
            self.path = p
            self.saveable = True
            self.saveasable = True
            self._load(p)

    def save(self):
        if self.path:
            if self._validate_sequence():
                self._save_file(self.path)

    def save_as(self):
        if self._validate_sequence():
            dialog = FileDialog(action='save as', default_directory=paths.hops_dir)
            if dialog.open() == OK:
                p = dialog.path
                self._save_file(p)

    def _load(self, p):
        with open(p, 'r') as fp:
            hops = [eval(l) for l in fileiter(fp)]
            self.hop_sequence = hs = HopSequence()
            for i, (hopstr, cnt, settle) in enumerate(hops):
                h = Hop(name=str(i + 1),
                        counts=cnt, settle=settle, detectors=self.detectors)
                h.parse_hopstr(hopstr)
                hs.hops.append(h)

    def _validate_sequence(self):
        hs = []
        for h in self.hop_sequence.hops:
            if not h.validate_hop():
                hs.append('Invalid Hop {}. {}'.format(h.name, h.error_message))
        if hs:
            self.warning_dialog('\n'.join(hs))
        else:
            return True

    def _save_file(self, p):
        p = add_extension(p, '.txt')
        header = '#hopstr e.i iso:det[:defl][,iso:det....], count, settle\n'
        txt = self.hop_sequence.to_string()
        self.info('saving hop to {}'.format(p))
        with open(p, 'w') as fp:
            fp.write(header)
            fp.write(txt)

        self.saveable = True

    def _add_hop_button_fired(self):
        idx = None
        if self.selected:
            idx = self.hop_sequence.hops.index(self.selected)

        self.hop_sequence.add_hop(idx)
        self.saveasable = True

    def _remove_hop_button_fired(self):
        idx = self.hop_sequence.hops.index(self.selected)
        self.hop_sequence.remove_hop(idx)
        if not self.hop_sequence.hops:
            self.saveasable = False


class HopEditorView(Controller):
    model = HopEditorModel

    def save(self, info):
        self.model.save()

    def save_as(self, info):
        self.model.save_as()

    def traits_view(self):
        cols = [ObjectColumn(name='name',
                             label='',
                             editable=False),
                ObjectColumn(name='counts'),
                ObjectColumn(name='settle')]

        hgrp = VGroup(
            UItem('object.hop_sequence.hops',
                  editor=myTableEditor(columns=cols,
                                       clear_selection_on_dclicked=True,
                                       sortable=False,
                                       selected='selected')),

            HGroup(icon_button_editor('add_hop_button', 'add',
                                      tooltip='Add peak hop'),
                   icon_button_editor('remove_hop_button', 'delete',
                                      tooltip='Delete selected peak hop',
                                      enabled_when='selected')))
        sgrp = UItem('selected', style='custom', editor=InstanceEditor())

        grp = HSplit(hgrp, sgrp)
        v = View(VGroup(CustomLabel('object.path'), grp, ),
                 toolbar=ToolBar(Action(name='Save',
                                        image=icon('document-save'),
                                        enabled_when='object.saveable',
                                        action='save'),
                                 Action(name='Save As',
                                        image=icon('document-save-as'),
                                        action='save_as',
                                        enabled_when='object.saveasable', )),
                 width=600,
                 title='Peak Hops Editor',
                 buttons=['OK', ],
                 resizable=True)
        return v


if __name__ == '__main__':
    m = HopEditorModel()
    h = HopEditorView(model=m)
    # m.new()
    m.open()
    h.configure_traits()


#============= EOF =============================================

