# ===============================================================================
# Copyright 2012 Jake Ross
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
import ConfigParser
import os

from pyface.timer.do_later import do_after
from traits.api import HasTraits, Str, List, Any, Event, Button, Int, Bool, Float
from traitsui.api import View, Item, HGroup, spring
from traitsui.handler import Handler
import yaml

from pychron.core.helpers.traitsui_shortcuts import listeditor



# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.loggable import Loggable
from pychron.paths import paths

DEFAULT_CONFIG = '''- name: HighVoltage
  min: 0
  max: 5000
- name: ElectronEnergy
  min: 0
  max: 10
- name: YSymmetry
  min: 0
  max: 10
- name: ZSymmetry
  min: 0
  max: 10
- name: ZFocus
  min: 0
  max: 10
- name: IonRepeller
  min: 0
  max: 10
- name: ExtractionLens
  min: 0
  max: 10
'''


class Readout(HasTraits):
    name = Str
    value = Str
    # value = Property(depends_on='refresh')
    format = Str('{:0.3f}')
    # refresh = Event
    spectrometer = Any

    min_value = Float(0)
    max_value = Float(100)

    def traits_view(self):
        v = View(HGroup(Item('value', style='readonly', label=self.name)))
        return v

    def set_value(self, v):
        self._set_value(v)

    def query_value(self):
        cmd = 'Get{}'.format(self.name)
        v = self.spectrometer.get_parameter(cmd)
        self._set_value(v)

    def _set_value(self, v):
        if v is not None:
            try:
                self._value = float(v)
                v = self.format.format(self._value)
            except ValueError:
                pass
        else:
            v = ''

        self.value = v

    def get_percent_value(self):
        return (self._value - self.min_value) / self.max_value


class ReadoutHandler(Handler):
    def closed(self, info, is_ok):
        info.object.stop()


class ReadoutView(Loggable):
    readouts = List(Readout)
    spectrometer = Any
    refresh = Button

    refresh_needed = Event
    refresh_period = Int(1, enter_set=True, auto_set=False)  # seconds
    use_word_query = Bool(True)

    _alive = False

    def __init__(self, *args, **kw):
        super(ReadoutView, self).__init__(*args, **kw)
        self._load()

    def _load(self):

        ypath = os.path.join(paths.spectrometer_dir, 'readout.yaml')
        if not os.path.isfile(ypath):
            path = os.path.join(paths.spectrometer_dir, 'readout.cfg')
            if os.path.isfile(path):
                self._load_cfg(path)
            else:
                if self.confirmation_dialog('no readout configuration file. \n'
                                            'Would you like to write a default file at {}'.format(ypath)):
                    self._write_default(ypath)
                    self._load_yaml(ypath)

        else:
            self._load_yaml(ypath)

        self._refresh()

    def _load_cfg(self, path):
        config = ConfigParser.ConfigParser()
        config.read(path)
        for section in config.sections():
            rd = Readout(name=section,
                         spectrometer=self.spectrometer)
            self.readouts.append(rd)

    def _load_yaml(self, path):
        with open(path, 'r') as rfile:
            try:
                yl = yaml.load(rfile)
                for rd in yl:
                    rr = Readout(spectrometer=self.spectrometer,
                                 name=rd['name'],
                                 min_value=rd.get('min', 0),
                                 max_value=rd.get('max', 1))
                    self.readouts.append(rr)

            except yaml.YAMLError:
                return

    def _write_default(self, ypath):
        with open(ypath, 'w') as wfile:
            wfile.write(DEFAULT_CONFIG)

    @property
    def ms_period(self):
        return self.refresh_period * 1000

    def start(self):
        self._alive = True
        self._refresh_loop()

    def stop(self):
        self._alive = False

    def _refresh_loop(self):
        self._refresh()
        if self._alive:
            do_after(self.ms_period, self._refresh_loop)

    def _refresh_fired(self):
        self._refresh()

    def _refresh(self):
        if self.use_word_query:
            keys = [r.name for r in self.readouts]
            ds = self.spectrometer.get_parameter_word(keys)
            for d, r in zip(ds, self.readouts):
                r.set_value(d)

        else:
            for rd in self.readouts:
                rd.query_value()
        self.refresh_needed = True

    def traits_view(self):
        v = View(listeditor('readouts'),
                 HGroup(spring, Item('refresh', show_label=False)))
        return v


def new_readout_view(spectrometer):
    rv = ReadoutView(spectrometer=spectrometer)
    rv.start()

    from traitsui.view import View
    from traitsui.api import UItem, VGroup, Item, HGroup

    from traitsui.table_column import ObjectColumn
    from traitsui.editors import TableEditor

    from pychron.processing.analyses.view.magnitude_editor import MagnitudeColumn

    cols = [ObjectColumn(name='name', label='Component'),
            ObjectColumn(name='value', label='Value'),
            MagnitudeColumn(name='value',
                            label='',
                            width=200), ]

    a = HGroup(Item('refresh_period', label='Period (s)'))
    b = UItem('readouts', editor=TableEditor(columns=cols, editable=False))
    from pychron.spectrometer.readout_view import ReadoutHandler

    v = View(VGroup(a, b),
             handler=ReadoutHandler(),
             title='Spectrometer Readout',
             width=500,
             resizable=True)
    return rv, v
# ============= EOF =============================================
