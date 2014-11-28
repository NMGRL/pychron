# ===============================================================================
# Copyright 2012 Jake Ross
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

#============= enthought library imports =======================
from traits.api import Int, Any, Str, Property, cached_property
from traitsui.api import View
#============= standard library imports ========================
import time
#============= local library imports  ==========================
from pychron.graph.graph import Graph
from pychron.saveable import Saveable


class DatabaseRecord(Saveable):
    selector = Any
    dbrecord = Property(depends_on='_dbrecord')
    _dbrecord = Any

    title = Property(depends_on='_dbrecord')
    title_str = Str
    summary = Str
#    id = Property

#    graph = Instance(Graph)

    rundate = Property
    runtime = Property

    timestamp = Property

    window_x = 0.1
    window_y = 0.1
    window_width = None
    window_height = None
    selector = Any

#    loadable = Property(depends_on='_loadable')
#    _loadable = Bool(True)
    record_id = Property

    resizable = True

    group_id = Int
    graph_id = Int

    def to_string(self):
        return str(self.record_id)

    @classmethod
    def make_timestamp(cls, rd, rt):
        timefunc = lambda xi: time.mktime(time.strptime(xi, '%Y-%m-%d %H:%M:%S'))
        ts = ' '.join((rd, rt))
        return timefunc(ts)

    def opened(self, ui):
        self.show()

#    def closed(self, isok):
#        self.closed_event = True
#    def load(self):
#        dbr = self._dbrecord
#        if dbr is not None:
#            self.title = '{} {}'.format(self.title_str, self.record_id)
#            self._load_hook(dbr)
#        elif self.filename is not None:
#        elif self.directory is not None and self.filename is not None:
#            self._load_hook('')

    def initialize(self):
        return True

    def load_graph(self):
        pass
#        dm = self.selector.data_manager
#        try:
#            l = dm.open_data(self._get_path(), caller='_get_loadable {}'.format(self))
#        except Exception, e:
#            import traceback
#            print traceback.print_exc()
#            l = False
#        finally:
#            pass
#
#        self._loadable = l
#        return self.loadable

# ===============================================================================
# private
# ===============================================================================

    def _load_hook(self, dbr):
        pass
# ===============================================================================
# property get/set
# ===============================================================================
    @cached_property
    def _get_loadable(self):
        return self._loadable

    def _get_record_id(self):
        if self.dbrecord:
            return self.dbrecord.id

    def _get_dbrecord(self):
        return self._dbrecord

    @cached_property
    def _get_timestamp(self):
        return self.dbrecord.timestamp

    @cached_property
    def _get_rundate(self):
        dbr = self.dbrecord
        if dbr and dbr.timestamp:
            date = dbr.timestamp.date()
            return date.strftime('%Y-%m-%d')

    @cached_property
    def _get_runtime(self):
        dbr = self.dbrecord
        if dbr and dbr.timestamp:
            ti = dbr.timestamp.time()
            return ti.strftime('%H:%M:%S')
#        return self.dbrecord
#        return self.make_timestamp(self.rundate, self.runtime)
#        timefunc = lambda xi: time.mktime(time.strptime(xi, '%Y-%m-%d %H:%M:%S'))
#        ts = ' '.join((self.rundate, self.runtime))
#        return timefunc(ts)
#    @cached_property
#    def _get_timestamp(self):
#        return ''
#        analysis = self.dbrecord
#        analts = analysis.timestamp
# #        analts = '{} {}'.format(analysis.rundate, analysis.runtime)
# #        analts = datetime.datetime.strptime(analts, '%Y-%m-%d %H:%M:%S')
#        return time.mktime(analts.timetuple())

#    @cached_property
#    def _get_rundate(self):
#        dbr = self.dbrecord
#        if dbr and dbr.rundate:
#            date = dbr.rundate
#            return date.strftime('%Y-%m-%d')
#
#    @cached_property
#    def _get_runtime(self):
#        dbr = self.dbrecord
#        if dbr and dbr.runtime:
#            ti = dbr.runtime
#            return ti.strftime('%H:%M:%S')
#        if dbr and dbr.timestamp:
#            ti = dbr.timestamp.time()
#            return ti.strftime('%H:%M:%S')

    def _get_title(self):
        return '{} {}'.format(self.title_str, self.record_id)

#    @cached_property
#    def _get_path(self):
#        if self._dbrecord:
#            if self._dbrecord.path:
#                root = self._dbrecord.path.root
#                name = self._dbrecord.path.filename
#                return os.path.join(root, name)

#    @property
#    @deprecated
#    def filename(self):
#        return os.path.basename(self.path)

#    def _export_button_fired(self):
#        self._export_csv()

# ===============================================================================
# factories
# ===============================================================================
    def _graph_factory(self, klass=None, width=500, height=300):
        if klass is None:
            klass = Graph
        g = klass(container_dict=dict(padding=[5, 5, 0, 0],
                                      spacing=0,
                                      bgcolor='green',
                                      fill_padding=False
                                      ),
                  width=width,
                  height=height
                  )

        return g
# ===============================================================================
# views
# ===============================================================================
#    def _get_additional_tabs(self):
#        return []
#
#    def _get_graph_item(self):
#        g = Item('graph',
#                    show_label=False,
#                    style='custom',
#                    height=1.0)
#        return g

#    def _get_info_grp(self):
#        return VGroup(
#                          VGroup(Item('rid', style='readonly', label='ID'),
#                                    Item('rundate', style='readonly', label='Run Date'),
#                                    Item('runtime', style='readonly', label='Run Time'),
#                                    Item('directory', style='readonly'),
#                                    Item('filename', style='readonly')),
#                            VGroup(Item('summary',
#                                    show_label=False,
#                                    style='readonly',
#                                    visible_when='object.summary'
#                                    )),
#                            HGroup(spring,
#                              Item('export_button',
#                                            show_label=False),
#                       visible_when='object.exportable'
#                       ),
# #                    label='Info',
#                    )

#    def traits_view(self):
#
#        grps = Group(self._get_info_grp())
# #        grps = Group()
#
#        agrps = self._get_additional_tabs()
#        g = self._get_graph_item()
#        if g is not None:
#            agrps.append(g)
#
#        for i, ai in enumerate(agrps):
#            grps.content.insert(i, ai)
#
#        return self._view_factory(grps)

    def _view_factory(self, grps):
        v = View(grps,
                    resizable=self.resizable,
                    x=self.window_x,
                    y=self.window_y,
                    title=self.title,
                    handler=self.handler_klass,
#                    buttons=[Action(name='Save', action='save')]
                    )

        if self.window_width:
            v.width = self.window_width
        if self.window_height:
            v.height = self.window_height
        return v


# ============= EOF =============================================
