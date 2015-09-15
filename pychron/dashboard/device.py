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
import random

from traits.api import Str, Bool, List, Instance, Event
from traitsui.api import View, ListEditor, InstanceEditor, UItem, VGroup, HGroup, VSplit
# ============= standard library imports ========================
import struct
import time
import yaml
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import unique_path2
from pychron.dashboard.conditional import DashboardConditional
from pychron.dashboard.process_value import ProcessValue
from pychron.globals import globalv
from pychron.graph.stream_graph import StreamStackedGraph
from pychron.hardware.core.i_core_device import ICoreDevice
from pychron.loggable import Loggable
from pychron.paths import paths


class DashboardDevice(Loggable):
    name = Str
    use = Bool

    values = List
    hardware_device = Instance(ICoreDevice)

    update_value_event = Event
    conditional_event = Event

    graph = Instance(StreamStackedGraph)

    @property
    def value_keys(self):
        return [pv.tag for pv in self.values]

    @property
    def units(self):
        return [pv.units for pv in self.values]

    @property
    def current_values(self):
        return [pv.last_value for pv in self.values]

    def setup_graph(self):
        self.graph = g = StreamStackedGraph()
        for i, vi in enumerate(self.values):
            vi.plotid = i
            p = g.new_plot()
            if i == 0:
                p.padding_bottom = 25
            p.padding_right = 10

            g.new_series(plotid=i)
            g.set_y_title(vi.display_name, plotid=i)
            g.set_scan_width(24 * 60 * 60, plotid=i)
            g.set_data_limits(24 * 60 * 60, plotid=i)

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
                    self._trigger(value, force=True)
            elif dt > value.period:
                self._trigger(value)

    def _trigger(self, value, **kw):
        try:
            self.debug('triggering value device={} value={} func={}'.format(self.hardware_device.name,
                                                                            value.name,
                                                                            value.func_name))
            nv = None
            func = getattr(self.hardware_device, value.func_name)
            if func is not None:
                nv = func(**kw)

            if nv is None and globalv.dashboard_simulation:
                nv = random.random()
            if nv is not None:
                self._push_value(value, nv)
        except BaseException:
            import traceback

            print self.hardware_device, self.hardware_device.name, value.func_name
            self.debug(traceback.format_exc())
            value.use_pv = False

    def add_value(self, name, tag, func_name, period, enabled, threshold, units, timeout, record, bindname):
        pv = ProcessValue(name=name,
                          tag=tag,
                          func_name=func_name,
                          period=period,
                          enabled=enabled,
                          timeout=float(timeout),
                          units=units,
                          change_threshold=threshold,
                          record=record)

        if period == 'on_change':
            self.debug('bind to {}'.format(bindname))
            if self.hardware_device:
                if bindname:
                    if hasattr(self.hardware_device, bindname):
                        self.hardware_device.on_trait_change(lambda a, b, c, d: self._handle_change(pv, a, b, c, d),
                                                             bindname)
                    else:
                        self.debug('{} has not attribute "{}"'.format(self.hardware_device, bindname))

                else:
                    self.warning('need to set bindname for {}'.format(self.name, name))
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

            pv.last_time = time.time()
            v = float(new)
            tripped = pv.is_different(v)
            if tripped:
                self.update_value_event = (pv.name, new, pv.units)
                # self.update_value_event = '{} {}'.format(pv.tag, new)

            self.graph.record(v, plotid=pv.plotid)
            if pv.record:
                self._record(pv, v)

            self._check_conditional(pv, new)

    def _record(self, pv, v):
        path = pv.path
        if not path:
            path, _ = unique_path2(paths.device_scan_dir, pv.name)
            pv.path = path
            self.info('Saving {} to {}'.format(pv.name, path))

        with open(path, 'a') as wfile:
            wfile.write('{},{}\n'.format(time.time(), v))

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
