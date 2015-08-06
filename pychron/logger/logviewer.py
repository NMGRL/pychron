# ===============================================================================
# Copyright 2015 Jake Ross
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
import re

from traits.api import HasTraits, Str, Bool, List, Event
from traitsui.api import View, UItem, Item, HGroup, VGroup, TabularEditor, Controller



# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter
from twisted.logger import eventsFromJSONLogFile
from pychron.core.helpers.datetime_tools import get_datetime
from pychron.pychron_constants import LIGHT_GREEN


class LogAdapter(TabularAdapter):
    columns = [('Timestamp', 'timestamp'),
               ('Level', 'level'),
               ('Message', 'message'), ]

    def get_bg_color(self, obj, trait, row, column=0):
        item = getattr(obj, trait)[row]
        # print item, item.found
        if item.found:
            c = LIGHT_GREEN
        else:
            c = 'white'

        return c


class LogItem:
    message = ''
    timestamp = ''
    level = ''
    found = False


name = r'(?P<name>^.{{1,{width}}}):'.format(width=40)
ts = r'(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})'
level = r'(?P<level>(INFO|DEBUG|WARNING|CRITICAL)\s{{1,{width}}})'.format(width=9)
thread = r'(?P<thread>\(.{{1,{width}}}\))'.format(width=10)
message = r'(?P<message>.*)'

regex = r' '.join((name, ts, level, thread, message))
regex = re.compile(regex)


class LogModel(HasTraits):
    items = List

    def _factory(self, line):
        li = LogItem()
        m = regex.match(line)
        if m:
            li.name = m.group('name').strip()
            li.timestamp = m.group('timestamp').strip()
            li.level = m.group('level').strip()
            li.thread = m.group('thread').strip()
            li.message = m.group('message').strip()
        else:
            li.message = line
        return li

    def open_file(self, path):
        with open(path, 'r') as rfile:
            self.items = self.oitems = [self._factory(line) for line in self._file(rfile)]

    def _file(self, r):
        return r


def tostr(vv):
    if isinstance(vv, (list, tuple)):
        vv = [str(vi) if isinstance(vi, unicode) else vi for vi in vv]
    else:
        vv = str(vv)
    return vv


class TwistedLogModel(LogModel):
    def _file(self, r):
        return eventsFromJSONLogFile(r)

    def _factory(self, ii):
        li = LogItem()
        li.level = ii.get('log_level')
        li.timestamp = get_datetime(ii.get('log_time'))

        fmt = ii.get('log_format')
        li.message = str(fmt.format(**{k: tostr(v) for k, v in ii.items()}))
        return li

        # def open_file(self, path):
        #     # output(event)
        #     self.cnt = 0
        #
        #
        #
        #     def factory(ii):
        #         li = LogItem()
        #
        #         li.level = ii.get('log_level')
        #         li.timestamp = get_datetime(ii.get('log_time'))
        #
        #         fmt = ii.get('log_format')
        #         li.message = str(fmt.format(**{k: tostr(v) for k, v in ii.items()}))
        #         return li
        #
        #     with open(path, 'r') as rfile:
        #         self.items = self.oitems = [factory(event) for event in eventsFromJSONLogFile(rfile)]


class LogViewer(Controller):
    search_entry = Str(enter_set=True, auto_set=False)
    refresh_needed = Event
    use_fuzzy = Bool(True)
    use_filter = Bool(True)

    def controller_search_entry_changed(self, info):
        v = self.search_entry
        if v:
            if self.use_fuzzy:
                pat = '.*?'.join(map(re.escape, v))
            else:
                pat = '^{}'.format(v)

            regex = re.compile(pat)
            if self.use_filter:
                self.model.items = filter(lambda x: regex.search(x.message), self.model.oitems)
            else:
                for i in self.model.oitems:
                    if regex.search(i.message):
                        i.found = True
                    else:
                        i.found = False
                self.model.items = self.model.oitems
        else:
            for i in self.model.items:
                i.found = False
        self.refresh_needed = True

    def traits_view(self):
        ctrlgrp = VGroup(HGroup(UItem('controller.search_entry'),
                                Item('controller.use_fuzzy'),
                                Item('controller.use_filter')))

        v = View(VGroup(ctrlgrp, UItem('items', editor=TabularEditor(adapter=LogAdapter(),
                                                                     refresh='controller.refresh_needed',
                                                                     operations=[]))),
                 resizable=True,
                 width=500,
                 height=700)
        return v


if __name__ == '__main__':
    # m = LogModel()
    # m.parse()
    # m.open_file('/Users/ross/Pychron_dev/logs/pychron-09932.log')
    m = TwistedLogModel()
    m.open_file('/Users/ross/Documents/pps.log.json')
    lv = LogViewer(model=m)
    lv.configure_traits()
# ============= EOF =============================================
