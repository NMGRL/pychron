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

from traits.api import Str, Bool, List, Instance, Event
from traitsui.api import View, ListEditor, InstanceEditor, UItem, VGroup, HGroup, VSplit
# ============= standard library imports ========================
import struct
import time
import yaml
# ============= local library imports  ==========================
from pychron.dashboard.conditional import DashboardConditional
from pychron.dashboard.constants import PUBLISH
from pychron.dashboard.process_value import ProcessValue
from pychron.graph.stream_graph import StreamStackedGraph
from pychron.hardware.core.i_core_device import ICoreDevice
from pychron.loggable import Loggable


class DashboardDevice(Loggable):
    name = Str
    use = Bool

    values = List
    _device = Instance(ICoreDevice)

    update_value_event = Event
    conditional_event = Event

    graph = Instance(StreamStackedGraph)

    def setup_graph(self):
        self.graph = g = StreamStackedGraph()
        for i, vi in enumerate(self.values):
            vi.plotid = i
            g.new_plot()
            g.new_series(plotid=i)
            g.set_y_title(vi.name, plotid=i)

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
            elif dt > value.period:
                try:
                    nv = getattr(self._device, value.func_name)()
                    self._push_value(value, nv)
                except Exception:
                    import traceback
                    print self._device, self._device.name, value.func_name
                    self.debug(traceback.format_exc(limit=2))
                    value.use_pv = False

    def add_value(self, n, tag, func_name, period, use, threshold, timeout):
        pv = ProcessValue(name=n,
                          tag=tag,
                          func_name=func_name,
                          period=period,
                          enabled=use,
                          timeout=timeout,
                          change_threshold=threshold)

        if period == 'on_change':
            self.debug('bind to {}'.format(n))
            if self._device:
                self._device.on_trait_change(lambda a, b, c, d: self._handle_change(pv, a, b, c, d), n)
                # self._device.on_trait_change(lambda new: self._push_value(pv, new), n)

        self.values.append(pv)
        return pv

    def add_conditional(self, pv, severity, **kw):
        cond = DashboardConditional(severity=severity, **kw)
        pv.conditionals.append(cond)

    def _handle_change(self, pv, obj, name, old, new):
        self.debug('handle change {} {}'.format(name, new))
        self._push_value(pv, new)

    def _push_value(self, pv, new):
        if pv.enabled:
            v = float(new)
            tripped = pv.is_different(v)
            if tripped:
                self.update_value_event = '{} {}'.format(pv.tag, new)

            self.graph.record(v, plotid=pv.plotid)
            self._check_conditional(pv, new)

    def _check_conditional(self, pv, new):
        conds = pv.conditionals
        if conds:
            if pv.flag:
                self.debug('not checking conditionals. already tripped')
            else:
                for cond in conds:
                    self.debug('checking conditional {}.{}.{}, value={}'.format(self.name, pv.name, cond.teststr, new))
                    if cond.check(new):
                        pv.flag = cond.severity
                        self.debug('conditional triggered. severity={}'.format(cond.severity))
                        msg = '{}.{}.{} is True. value={}'.format(self.name, pv.name, cond.teststr, new)
                        self.conditional_event = '{}|{}|{}|{}'.format(cond.severity,
                                                                      cond.script,
                                                                      cond.emails, msg)

    def dump_meta(self):
        d = []

        for pv in self.values:
            dd = dict(((a, getattr(pv, a))
                       for a in ('name', 'tag', 'enabled', 'func_name', 'period', 'timeout')))
            d.append(dd)
        return yaml.dump(d)

    def get_scan_fmt(self):
        n = len(self.values) * 2
        fmt = '>{}'.format('f' * n)
        return fmt

    def append_scan_blob(self, blob=None, fmt=None):
        new_args = [a for v in self.values
                    for a in (v.last_time, v.last_value)]

        if blob:
            step = 4 * fmt.count('f')
            args = zip(*[struct.unpack(fmt, blob[i:i + step]) for i in xrange(0, len(blob), step)])
            ns = []
            for blobv, lastv in zip(args, new_args):
                blobv = list(blobv)
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
        ggrp = UItem('graph', style='custom')
        v = View(VGroup(hgrp,
                        VSplit(dgrp,
                               ggrp)))
        return v

# ============= EOF =============================================
