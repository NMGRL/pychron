# ===============================================================================
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
# ===============================================================================
from pychron.core.ui import set_qt
from pychron.envisage.icon_button_editor import icon_button_editor

set_qt()

from pyface.confirmation_dialog import ConfirmationDialog

# ============= enthought library imports =======================
from traitsui.handler import Controller
from traitsui.table_column import ObjectColumn
from pyface.constant import OK, CANCEL, YES
from pyface.file_dialog import FileDialog
from traits.api import HasTraits, Str, List, Int, Any, Button, Bool, on_trait_change, Instance
from traitsui.menu import Action
from traitsui.api import View, Item, UItem, HGroup, InstanceEditor, HSplit, VGroup, EnumEditor

# ============= standard library imports ========================
import os
# ============= local library imports  ==========================
from pychron.core.ui.text_editor import myTextEditor
from pychron.paths import paths
from pychron.envisage.resources import icon
from pychron.core.helpers.filetools import fileiter, add_extension
from pychron.experiment.automated_run.hop_util import split_hopstr
from pychron.loggable import Loggable
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
    isotope_label = Str
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

        self._handle_position_change()

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
        idx = self.positions.index(self.selected)

        self.positions.remove(self.selected)

        if len(self.positions) > 0:
            self.selected = self.positions[idx - 1]
        else:
            self.selected = None

    @on_trait_change('positions:isotope, positions[]')
    def _handle_position_change(self):
        self.isotopes_label = ','.join([i.isotope for i in self.positions])

    def traits_view(self):
        from pychron.pychron_constants import ISOTOPES

        cols = [
            ObjectColumn(name='name', label='', width=20, editable=False),
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
            print hi.name
            for j, pi in enumerate(hi.positions):
                pi.name = str(j + 1)

    def remove_hop(self, idx):
        self.hops.pop(idx)
        self._label_hops()

    def label_hops(self):
        self._label_hops()


class HopEditorModel(Loggable):
    hop_sequence = Instance(HopSequence)
    selected = Any
    path = Str
    detectors = List
    add_hop_button = Button
    remove_hop_button = Button
    # saveable = Bool
    # saveasable = Bool
    text = Str
    dirty = Bool

    def new(self):
        self.hop_sequence = HopSequence()

    def open(self, p=None):
        if p is None:
            p = '/Users/ross/Pychrondata_dev/scripts/measurement/hops/hop.txt'

        if not os.path.isfile(p):
            p = ''
            dialog = FileDialog(action='open', default_directory=paths.hops_dir)
            if dialog.open() == OK:
                p = dialog.path

        if os.path.isfile(p):
            self.path = p
            # self.saveable = True
            # self.saveasable = True
            self._load(p)

    def save(self):
        if self.path:
            if self._validate_sequence():
                self._save_file(self.path)
        else:
            self.save_as()

    def save_as(self):
        if self._validate_sequence():
            dialog = FileDialog(action='save as', default_directory=paths.hops_dir)
            if dialog.open() == OK:
                p = dialog.path
                p = add_extension(p, '.txt')
                self._save_file(p)
                self.path = p

    def _load(self, p):
        with open(p, 'r') as rfile:
            hops = [eval(l) for l in fileiter(rfile)]
            self.hop_sequence = hs = HopSequence()
            for i, (hopstr, cnt, settle) in enumerate(hops):
                h = Hop(name=str(i + 1),
                        counts=cnt, settle=settle, detectors=self.detectors)
                h.parse_hopstr(hopstr)
                hs.hops.append(h)
            hs.label_hops()

        self.selected = hs.hops[0]

        with open(p, 'r') as rfile:
            self.text = rfile.read()

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

        # header = '#hopstr e.i iso:det[:defl][,iso:det....], count, settle\n'
        # txt = self.hop_sequence.to_string()
        self.info('saving hop to {}'.format(p))
        with open(p, 'w') as wfile:
            wfile.write(self.to_string())
            # wfile.write(header)
            # wfile.write(txt)

        # self.saveable = True

        with open(p, 'r') as rfile:
            self.text = rfile.read()
        self.dirty = False

    def to_string(self):
        header1 = "#hopstr ('iso:det[:defl][,iso:det....]', count, settle)"
        header2 = "#e.g ('Ar40:H1, Ar41:H2, Ar38:L1, Ar37:L2, Ar36:CDD:110', 15, 3)"

        return '\n'.join((header1, header2, self.hop_sequence.to_string()))

    def _add_hop_button_fired(self):
        idx = None
        if self.selected:
            idx = self.hop_sequence.hops.index(self.selected)

        self.hop_sequence.add_hop(idx)
        # self.saveasable = True
        self.dirty = True

    def _remove_hop_button_fired(self):
        hops = self.hop_sequence.hops
        idx = hops.index(self.selected)
        if len(hops) > 1:
            self.selected = hops[0]
        else:
            self.selected = None

        self.hop_sequence.remove_hop(idx)
        self.dirty = True
        # if not self.hop_sequence.hops:
        #     self.saveasable = False
        #     self.saveable = False


class HopEditorView(Controller):
    model = HopEditorModel
    title = Str('Peak Hops Editor')

    def close(self, info, is_ok):
        if self.model.dirty:
            dlg = ConfirmationDialog(message='Save changes to Hops file', cancel=True,
                                     default=CANCEL, title='Save Changes?')
            ret = dlg.open()
            if ret == CANCEL:
                return False
            elif ret == YES:
                self.model.save()
        return True

    @on_trait_change('model:hop_sequence:hops:[counts,settle, positions:[isotope,detector,deflection]]')
    def _handle_edit(self):
        self.model.dirty = True
        self.model.text = self.model.to_string()

    @on_trait_change('model.[path,dirty]')
    def _handle_path_change(self):
        p = self.model.path

        n = os.path.basename(p)
        if self.model.dirty:
            n = '*{}'.format(n)

        d = os.path.dirname(p)
        d = d.replace(os.path.expanduser('~'), '')
        t = '{} - PeakHop Editor - {}'.format(n, d)
        if not self.info:
            self.title = t
        else:
            self.info.ui.title = t

    def save(self, info):
        self.model.save()

    def save_as(self, info):
        self.model.save_as()

    def traits_view(self):
        cols = [ObjectColumn(name='name',
                             label='',
                             editable=False),
                ObjectColumn(name='counts'),
                ObjectColumn(name='settle', label='Settle (s)'),
                ObjectColumn(name='isotopes_label',
                             editable=False,
                             width=175,
                             label='Isotopes')]

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
        save_action = Action(name='Save',
                             image=icon('document-save'),
                             enabled_when='object.saveable',
                             action='save')
        save_as_acion = Action(name='Save As',
                               image=icon('document-save-as'),
                               action='save_as',
                               enabled_when='object.saveasable', )

        teditor = myTextEditor(bgcolor='#F7F6D0',
                               fontsize=12,
                               fontsize_name='fontsize',
                               wrap=False,
                               tab_width=15)

        v = View(VGroup(VGroup(grp, label='Editor'),
                        VGroup(UItem('object.text',
                                     editor=teditor,
                                     style='custom'), label='Text')),
                 # toolbar=ToolBar(),
                 width=690,
                 title=self.title,
                 buttons=['OK', save_action, save_as_acion],
                 resizable=True)
        return v


if __name__ == '__main__':
    m = HopEditorModel()
    m.detectors = ['H2', 'H1', 'CDD']
    m.open()
    h = HopEditorView(model=m)
    # m.new()
    h.configure_traits()


# ============= EOF =============================================
