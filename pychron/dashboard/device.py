#===============================================================================
# Copyright 2013 Jake Ross
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

#============= enthought library imports =======================
import struct
from traits.api import HasTraits, Str, Either, Float, Property, Bool, List, Instance, \
    Event
from traitsui.api import View, Item, ListEditor, InstanceEditor, UItem, VGroup, HGroup

#============= standard library imports ========================
import time
#============= local library imports  ==========================
import yaml
from pychron.hardware.core.i_core_device import ICoreDevice
from pychron.core.helpers.datetime_tools import convert_timestamp
from pychron.loggable import Loggable


class ProcessValue(HasTraits):
    name = Str
    tag = Str
    func_name = Str

    period = Either(Float, Str) #"on_change" or number of seconds
    last_time = Float
    last_time_str = Property(depends_on='last_time')
    enabled = Bool
    last_value = Float
    timeout = Float

    def traits_view(self):
        v = View(VGroup(HGroup(UItem('enabled'), Item('name')),
                        VGroup(Item('tag'),
                               Item('period'),
                               Item('last_time_str', style='readonly'),
                               Item('last_value', style='readonly'),
                               enabled_when='enabled')))
        return v

    def _get_last_time_str(self):
        r = ''
        if self.last_time:
            r = convert_timestamp(self.last_time)

        return r


class DashboardDevice(Loggable):
    name = Str
    use = Bool

    values = List
    _device = Instance(ICoreDevice)

    publish_event = Event

    def trigger(self):
        """
            trigger a new value if appropriate
        """

        for value in self.values:
            if not value.enabled:
                continue

            st = time.time()
            dt = st - value.last_time
            if value.period == 'on_change':
                if value.timeout and dt > value.timeout:
                    self._push_value(value, 'timeout')

                continue

            if dt > value.period:
                try:
                    nv = getattr(self._device, value.func_name)()
                    self._push_value(value, nv)
                except Exception:
                    import traceback

                    self.debug(traceback.format_exc(limit=2))
                    value.use_pv = False

    def add_value(self, n, tag, func_name, period, use, timeout):
        pv = ProcessValue(name=n,
                          tag=tag,
                          func_name=func_name,
                          period=period,
                          enabled=use,
                          timeout=timeout)

        if period == 'on_change':
            self.debug('bind to {}'.format(n))
            if self._device:
                self._device.on_trait_change(lambda a, b, c, d: self._handle_change(pv, a, b, c, d), n)
            #self._device.on_trait_change(lambda new: self._push_value(pv, new), n)

        self.values.append(pv)

    def _handle_change(self, pv, obj, name, old, new):
        self.debug('handle change {} {}'.format(name, new))
        self._push_value(pv, new)

    def _push_value(self, pv, new):
        if pv.enabled:
            tag = pv.tag
            self.publish_event = '{} {}'.format(tag, new)
            pv.last_value = float(new)
            pv.last_time = time.time()

    def dump_meta(self):
        d=[]

        for pv in self.values:
            dd=dict(((a,getattr(pv, a))
                        for a in ('name', 'tag', 'enabled', 'func_name', 'period', 'timeout')))
            d.append(dd)
        return yaml.dump(d)

    def get_scan_fmt(self):
        n=len(self.values) *2
        fmt = '>{}'.format('f' * n)
        return fmt

    def append_scan_blob(self, blob=None, fmt=None):
        new_args = [a for v in self.values
                    for a in (v.last_time, v.last_value)]

        if blob:
            step = 4 * fmt.count('f')
            args = zip(*[struct.unpack(fmt, blob[i:i + step]) for i in xrange(0, len(blob), step)])
            ns=[]
            for blobv, lastv in zip(args, new_args):
                blobv=list(blobv)
                blobv.append(lastv)
                ns.append(blobv)
            blob = ''.join([struct.pack(fmt, *v) for v in zip(*ns)])
        else:
            fmt = '>{}'.format('f' * len(new_args))
            blob = struct.pack(fmt, *new_args)

        return blob

    def traits_view(self):
        hgrp = HGroup(UItem('use'), UItem('name', style='readonly'))
        dgrp = VGroup(UItem('values',
                            editor=ListEditor(editor=InstanceEditor(),
                                              style='custom',
                                              mutable=False), ),
                      show_border=True,
                      enabled_when='use')
        v = View(VGroup(hgrp,
                        dgrp))
        return v

#============= EOF =============================================
