# ===============================================================================
# Copyright 2011 Jake Ross
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

# =============enthought library imports=======================
from traits.api import HasTraits, Str, List, Float, Property, Tuple, Bool, Instance
from traitsui.api import View, Item, HGroup, ListEditor, InstanceEditor
# =============standard library imports ========================
from numpy import polyval
from pychron.hardware.agilent.agilent_unit import AgilentUnit
# =============local library imports  ==========================
# from pychron.hardware.adc.analog_digital_converter import AnalogDigitalConverter


class Equation(HasTraits):
    def get_value(self, v):
        return v


class Polynomial(Equation):
    coefficients = Tuple

    def get_value(self, v):
        cf = self.coefficients
        if not cf:
            cf = (1, 0)

        return polyval(cf, v)


class Boolean(Equation):
    threshold = Float
    inverted_logic = Bool

    def get_value(self, v):
        o = v > self.threshold
        if self.inverted_logic:
            o = not o
        return 'ON' if o else 'OFF'


class Channel(HasTraits):
    address = Str
    name = Str
    value = Float
    process_value = Property(depends_on='value')
    kind = Str('DC')
    equation = Instance(Equation, ())

    def traits_view(self):
        v = View(HGroup(Item('name', show_label=False, style='readonly', width=200),
                        Item('address', show_label=False, style='readonly', width=75),
                        Item('value', show_label=False, style='readonly', width=100),
                        Item('process_value', show_label=False, style='readonly', width=100)))
        return v

    def _get_process_value(self):
        return self.equation.get_value(self.value)


#        value = self.value
#        if self.coefficients:
#            value = polyval(self.coefficients, value)
#        return value

class AgilentMultiplexer(AgilentUnit):
    channels = List

    scan_func = 'channel_scan'

    def load_additional_args(self, config):
        ret = super(AgilentMultiplexer, self).load_additional_args(config)
        if not ret:
            return

        # load channels
        self.channels = []
        for section in config.sections():
            if section.startswith('Channel'):
                kind = self.config_get(config, section, 'kind', default='DC')
                name = self.config_get(config, section, 'name', default='')

                threshold = self.config_get(config, section, 'threshold', cast='float', default=None)
                if threshold is not None:
                    inv = self.config_get(config, section, 'inverted_logic', cast='boolean', default=False)
                    eq = Boolean(threshold=threshold, inverted_logic=inv)
                else:
                    cs = self.config_get(config, section, 'coefficients', default='1,0')
                    try:
                        cs = map(float, cs.split(','))
                    except ValueError:
                        self.warning('invalid coefficients for {}. {}'.format(section, cs))
                        cs = 1, 0
                    eq = Polynomial(coefficients=cs)

                ch = Channel(address='{}{:02d}'.format(self.slot, int(section[7:])),
                             kind=kind,
                             name=name,
                             equation=eq)
                self.channels.append(ch)

                # self._update_channels = True
        return True

    def initialize(self, *args, **kw):
        """
        """
        super(AgilentMultiplexer, self).initialize(*args, **kw)

        # cmds = (
        #              'FORM:READING:ALARM OFF',
        #              'FORM:READING:CHANNEL ON',
        #              'FORM:READING:TIME OFF',
        #              'FORM:READING:UNIT OFF',
        #              #'ROUT:CHAN:DELAY {} {}'.format(0.05, self._make_scan_list()),
        #              'TRIG:COUNT {}'.format(self.trigger_count),
        #              'TRIG:SOURCE TIMER',
        #              'TRIG:TIMER 0',
        #              'ROUT:SCAN {}'.format(self.make_scan_list()),
        #             )
        #        for c in cmds:
        #            self.tell(c)

        # configure channels
        # configure volt changes
        #        chs = self._get_dc_channels()
        # c = 'CONF:VOLT:DC {}'.format(self.make_scan_list(chs))
        #        self.tell(c)

        # configure channels
        for tag, chs in (('VOLT:DC', self._get_dc_channels()),
                         ('TEMP:TC', self._get_tc_channels())):
            if chs:
                self.tell('CONF:{} {}'.format(tag, self.make_scan_list(chs)))

        return True

    def channel_scan(self, **kw):
        verbose = False
        self._trigger(verbose=verbose)
        pts = self._wait(verbose=verbose)
        if pts:
            rs = []
            n = len(self.channels)
            for i, ci in enumerate(self.channels):
                v = self.ask('DATA:REMOVE? {}'.format(pts), verbose=verbose)
                try:
                    ci.value = float(v)
                    rs.append(v)
                except ValueError:
                    rs = []
                    break

                if i == n - 1:
                    break
                else:
                    pts = self._wait(n=5, verbose=verbose)
                    if not pts:
                        break

            return ','.join(rs)

    def read_channel(self, name):
        # if device is not scanning force a channel scan
        # otherwise use the last scan value
        if not self._scanning:
            self.channel_scan()

        channel = self._get_channel(name)
        if channel is not None:
            return channel.value

    def make_scan_list(self, channels=None):
        if channels is None:
            channels = self.channels

        return '(@{})'.format(','.join([ci.address for ci in channels]))

    # ===============================================================================
    # view
    # ===============================================================================
    def traits_view(self):
        v = View(Item('channels', show_label=False,
                      height=400,
                      editor=ListEditor(mutable=False,
                                        editor=InstanceEditor(), style='custom')))
        return v

    # ===============================================================================
    # private
    # ===============================================================================
    def _get_dc_channels(self):
        return [ci for ci in self.channels if ci.kind == 'DC']

    def _get_tc_channels(self):
        return [ci for ci in self.channels if ci.kind == 'TC']

    def _get_channel(self, name):
        return next((chan for chan in self.channels
                     if chan.name == name or \
                     chan.address[1:] == name), None)


#    def _get_channels(self):
# #        print 'asdfasdfasdfsadfsda', len(self._channels)
#        return self._channels


class AgilentSingleADC(AgilentUnit):
    '''
    '''
    #    def __init__(self, *args, **kw):
    # super(AgilentADC, self).__init__(*args, **kw)
    #    address = None

    def load_additional_args(self, config):
        '''

        '''
        super(AgilentSingleADC, self).load_additional_args(config)
        channel = self.config_get(config, 'General', 'channel', cast='int')

        if self.slot is not None and channel is not None:
            self.address = '{}{:02d}'.format(self.slot, channel)
            return True

    def initialize(self, *args, **kw):
        '''
        '''
        super(AgilentSingleADC, self).initialize(*args, **kw)

        cmds = [
            'CONF:VOLT:DC {}'.format(self.make_scan_list()),
            # 'FORM:READING:ALARM OFF',
            #              'FORM:READING:CHANNEL ON',
            #              'FORM:READING:TIME OFF',
            #              'FORM:READING:UNIT OFF',
            #              'TRIG:SOURCE TIMER',
            #              'TRIG:TIMER 0',
            #              'TRIG:COUNT {}'.format(self.trigger_count),
            #              'ROUT:SCAN (@{})'.format(self.address)
        ]

        for c in cmds:
            self.tell(c)

        return True

    def _make_scan_list(self):
        return '(@{})'.format(self.address)

    def read_device(self, **kw):
        '''
        '''
        self._trigger()
        pts = self._wait()
        if pts:
            resp = self.ask('DATA:REMOVE? {}'.format(pts))
            resp = self._parse_response(resp)
            return resp

        #        resp = self.ask('DATA:POINTS?')
            # if resp is not None:
            #            n = float(resp)
            #            resp = 0
            #            if n > 0:
            #                resp = self.ask('DATA:REMOVE? {}'.format(float(n)))
            #                resp = self._parse_response_(resp)

            # self.current_value = resp
            #            self.read_voltage = resp
            # return resp

    def _parse_response_(self, r):
        '''
            
        '''
        if r is None:
            return r

        return float(r)

#        args = r.split(',')
#        data = args[:-1]

#        return sum([float(d) for d in data]) / self.trigger_count



# ============= EOF =====================================
