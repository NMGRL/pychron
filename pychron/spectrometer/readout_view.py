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

DEFAULT_CONFIG = '''-
  - name: HighVoltage
    min: 0
    max: 5
    compare: False
  - name: ElectronEnergy
    min: 53
    max: 153
    compare: False
  - name: YSymmetry
    min: -100
    max: 100
    compare: True
  - name: ZSymmetry
    min: -100
    max: 100
    compare: True
  - name: ZFocus
    min: 0
    max: 100
    compare: True
  - name: IonRepeller
    min: -22.5
    max: 53.4
    compare: True
  - name: ExtractionLens
    min: 0
    max: 100
    compare: True

-
  - name: H2
    compare: True
  - name: H1
    compare: True
  - name: AX
    compare: True
  - name: L1
    compare: True
  - name: L2
    compare: True
  - name: CDD
    compare: True
'''


class BaseReadout(HasTraits):
    name = Str
    value = Float
    spectrometer = Any
    compare = Bool(True)

    def set_value(self, v):
        try:
            self.value = float(v)
        except (AttributeError, ValueError, TypeError):
            pass


class Readout(BaseReadout):
    # value = Property(depends_on='refresh')
    # format = Str('{:0.3f}')
    # refresh = Event

    min_value = Float(0)
    max_value = Float(100)

    def traits_view(self):
        v = View(HGroup(Item('value', style='readonly', label=self.name)))
        return v


        # self._set_value(v)

    def query_value(self):
        cmd = 'Get{}'.format(self.name)
        v = self.spectrometer.get_parameter(cmd)
        self.set_value(v)
        # self._set_value(v)

    # def _set_value(self, v):
    # if v is not None:
    # try:
    #             self.fvalue = float(v)
    #             v = self.format.format(self.fvalue)
    #         except ValueError:
    #             pass
    #     else:
    #         v = ''
    #
    #     self.value = v

    def get_percent_value(self):
        return (self.value - self.min_value) / (self.max_value - self.min_value)


class DeflectionReadout(BaseReadout):
    pass


class ReadoutHandler(Handler):
    def closed(self, info, is_ok):
        info.object.stop()


class ReadoutView(Loggable):
    readouts = List(Readout)
    deflections = List(DeflectionReadout)
    spectrometer = Any
    refresh = Button

    refresh_needed = Event
    refresh_period = Int(10, enter_set=True, auto_set=False)  # seconds
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

            # self._refresh()

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
                yt = yaml.load(rfile)
                yl, yd = yt

                for rd in yl:
                    rr = Readout(spectrometer=self.spectrometer,
                                 name=rd['name'],
                                 min_value=rd.get('min', 0),
                                 max_value=rd.get('max', 1),
                                 compare=rd.get('compare', True))
                    self.readouts.append(rr)

                for rd in yd:
                    rr = DeflectionReadout(spectrometer=self.spectrometer,
                                           name=rd['name'],
                                           compare=rd.get('compare', True))
                    self.deflections.append(rr)

            except yaml.YAMLError:
                return

    def _write_default(self, ypath):
        with open(ypath, 'w') as wfile:
            wfile.write(DEFAULT_CONFIG)

    @property
    def ms_period(self):
        return self.refresh_period * 1000

    def start(self):
        if not self._alive:
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

            keys = [r.name for r in self.deflections]
            ds = self.spectrometer.get_deflection_word(keys)
            for d, r in zip(ds, self.deflections):
                r.set_value(d)

        else:
            for rd in self.readouts:
                rd.query_value()

        self.refresh_needed = True

        # compare to configuration values
        ne = []
        nd = []
        tol = 0.001

        spec = self.spectrometer
        for nn, rs in ((ne, self.readouts), (nd, self.deflections)):
            for r in rs:
                if not r.compare:
                    continue

                name = r.name
                rv = r.value
                cv = spec.get_configuration_value(name)
                if abs(rv - cv) > tol:
                    nn.append((r.name, rv, cv))
                    self.debug('{} does not match. Current:{:0.3f}, Config: {:0.3f}'.format(name, rv, cv))
        ns = ''
        if ne:
            ns = '\n'.join(map(lambda n: '{:<16s}\t{:0.3f}\t{:0.3f}'.format(*n), ne))

        if nd:
            nnn = '\n'.join(map(lambda n: '{:<16s}\t\t{:0.0f}\t{:0.0f}'.format(*n), nd))
            ns = '{}\n{}'.format(ns, nnn)

        if ns:
            msg = 'There is a mismatch between the current spectrometer values and the configuration.\n' \
                  'Would you like to set the spectrometer to the configuration values?\n\n' \
                  'Name\t\tCurrent\tConfig\n{}'.format(ns)
            if self.confirmation_dialog(msg, size=(725, 300)):
                self.spectrometer.send_configuration()
                self.spectrometer.set_debug_configuration_values()

    def traits_view(self):
        v = View(listeditor('readouts'),
                 HGroup(spring, Item('refresh', show_label=False)))
        return v


def new_readout_view(rv):
    rv.start()

    from traitsui.api import UItem, VGroup, Item, HGroup, View, TableEditor, Tabbed

    from traitsui.table_column import ObjectColumn

    from pychron.processing.analyses.view.magnitude_editor import MagnitudeColumn

    cols = [ObjectColumn(name='name', label='Name'),
            ObjectColumn(name='value', format='%0.3f', label='Value'),
            MagnitudeColumn(name='value',
                            label='',
                            width=200), ]
    dcols = [ObjectColumn(name='name', label='Name', width=100),
             ObjectColumn(name='value', label='Value', width=100)]

    a = HGroup(Item('refresh_period', label='Period (s)'))
    b = VGroup(UItem('readouts', editor=TableEditor(columns=cols, editable=False)), label='General')
    c = VGroup(UItem('deflections', editor=TableEditor(columns=dcols,
                                                       sortable=False,
                                                       editable=False)), label='Deflections')
    from pychron.spectrometer.readout_view import ReadoutHandler

    v = View(VGroup(a, Tabbed(b, c)),
             handler=ReadoutHandler(),
             title='Spectrometer Readout',
             width=500,
             resizable=True)
    return v

# ============= EOF =============================================
