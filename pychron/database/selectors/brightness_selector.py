# '''
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
# '''
## ============= enthought library imports =======================
# from traits.api import Str, String, Date, Time, Instance
## ============= standard library imports ========================
## ============= local library imports  ==========================
# from pychron.database.core.database_selector import DBSelector, DBResult
# from pychron.database.orms.co2laser_orm import PowerTable
# #from pychron.managers.data_managers.h5_data_manager import H5DataManager
# from pychron.graph.graph import Graph
#
#
# class PowerResult(DBResult):
#    rundate = Date
#    runtime = Time
#
#    directory = Str
#    filename = Str
#    window_x = 0.1
#    window_y = 0.1
#    title = Str
#    summary = Str
#    graph = Instance(Graph)
#
# #    def load_graph(self):
# #        data = os.path.join(self.directory, self.filename)
# #        from pychron.data_processing.power_mapping.power_map_processor import PowerMapProcessor
# #        pmp = PowerMapProcessor()
# ##        print os.path.isfile(data), data
# #        if data.endswith('.h5'):
# #            dm = H5DataManager()
# #            dm.open_data(data)
# #            reader = dm
# #        else:
# #            with open(data, 'r') as f:
# #                reader = csv.reader(f)
# #                #trim off header
# #                reader.next()
# #        self.graph = pmp.load_graph(reader)
# #
# #
# #    def load(self):
# #        dbr = self._db_result
# #        if dbr is not None:
# #            self._id = dbr.id
# #            self.rundate = dbr.rundate
# #            self.runtime = dbr.runtime
# #            p = dbr.path
# #            if p is not None:
# #                self.directory = p.root
# #                self.filename = p.filename
# #
# #            self.title = 'PowerMap {}'.format(self._id)
# #
# #    def traits_view(self):
# #        interface_grp = VGroup(
# #                          VGroup(Item('_id', style='readonly', label='ID'),
# #                    Item('rundate', style='readonly', label='Run Date'),
# #                    Item('runtime', style='readonly', label='Run Time'),
# #                    Item('directory', style='readonly'),
# #                    Item('filename', style='readonly')),
# #                VGroup(Item('summary',
# #                            show_label=False,
# #                            style='readonly')),
# #                    label='Info',
# #                    )
# #
# #        return View(
# #                    Group(
# #                    interface_grp,
# #                    Item('graph', width=0.75, show_label=False,
# #                         style='custom'),
# #                    layout='tabbed'
# #                    ),
# #
# #                    width=800,
# #                    height=0.85,
# #                    resizable=True,
# #                    x=self.window_x,
# #                    y=self.window_y,
# #                    title=self.title
# #                    )
#
#
# class PowerSelector(DBSelector):
#    parameter = String('PowerTable.rundate')
#    date_str = 'rundate'
#
#    def _get__parameters(self):
#
#        b = PowerTable
#
#        f = lambda x:[str(col)
#                           for col in x.__table__.columns]
#        params = f(b)
#        return list(params)
#
#    def _dclicked_fired(self):
#        s = self.selected
#
#        if s is not None:
#            for si in s:
#                sid = si._id
#                if sid in self.opened_windows:
#                    c = self.opened_windows[sid].control
#                    if c is None:
#                        self.opened_windows.pop(sid)
#                    else:
#                        try:
#                            c.Raise()
#                        except:
#                            self.opened_windows.pop(sid)
#
#                else:
#                    try:
#                        si.load_graph()
#                        si.window_x = self.wx
#                        si.window_y = self.wy
#
#                        info = si.edit_traits()
#                        self.opened_windows[sid] = info
#
#                        self.wx += 0.005
#                        self.wy += 0.03
#
#                        if self.wy > 0.65:
#                            self.wx = 0.4
#                            self.wy = 0.1
#                    except Exception, e:
#                        self.warning(e)
#
#    def _execute_(self):
#        db = self._db
#        if db is not None:
# #            self.info(s)
#            s = self._get_filter_str()
#            if s is None:
#                return
#
#            table, _col = self.parameter.split('.')
#            kw = dict(filter_str=s)
#            if not table == 'BrightnessTable':
#                kw['join_table'] = table
#
#            dbs = db.get_brightness_s(**kw)
#
#            self.info('query {} returned {} results'.format(s,
#                                    len(dbs) if dbs else 0))
#            if dbs:
#                self.results = []
#                for di in dbs:
#                    d = PowerResult(_db_result=di)
#                    d.load()
#                    self.results.append(d)
#
## ============= EOF =============================================
