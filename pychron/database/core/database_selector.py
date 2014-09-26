#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from datetime import datetime, timedelta

from traits.api import Button, List, Any, Dict, Bool, Int, Enum, Event, \
    on_trait_change, Str, Instance, Property
from traitsui.api import View, Item, \
    HGroup, spring, ListEditor, InstanceEditor, Handler, VGroup, VSplit


#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.core.progress import progress_loader
from pychron.database.core.database_adapter import DatabaseAdapter

from pychron.database.core.query import Query, compile_query
from pychron.viewable import Viewable

from pychron.core.ui.tabular_editor import myTabularEditor
# from pychron.database.core.base_results_adapter import BaseResultsAdapter
from pychron.core.ui.custom_label_editor import CustomLabel
from traitsui.tabular_adapter import TabularAdapter
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.column_sorter_mixin import ColumnSorterMixin


class BaseTabularAdapter(TabularAdapter):
    columns = [('ID', 'record_id'),
               ('Timestamp', 'timestamp')]

# class ColumnSorterMixin(HasTraits):
#     _sort_field = None
#     _reverse_sort = False
#     column_clicked = Any
#
#     def _column_clicked_changed(self, event):
#         values = event.editor.value
#
#         fields = [name for _, name in event.editor.adapter.columns]
#         field = fields[event.column]
#         self._reverse_sort = not self._reverse_sort
#
#         self._sort_columns(values, field)
#
#     def _sort_columns(self, values, field=None):
#         # get the field to sort on
#         if field is None:
#             field = self._sort_field
#             if field is None:
#                 return
#
#         values.sort(key=lambda x: getattr(x, field),
#                     reverse=self._reverse_sort)
#         self._sort_field = field


class SelectorHandler(Handler):
    def init(self, info):
        pass

        # #        if info.initialized:


class DatabaseSelector(Viewable, ColumnSorterMixin):
    records = List
    num_records = Property(depends_on='records')

    search = Button
    dclick_recall_enabled = Bool(False)

    db = Instance(DatabaseAdapter)
    tabular_adapter_klass = BaseTabularAdapter
    tabular_adapter = Any  #Instance(BaseTabularAdapter
    id_string = Str
    title = ''

    dclicked = Any
    selected = Any
    scroll_to_row = Int
    scroll_to_bottom = True
    key_pressed = Event

    update = Event
    selected_row = Any

    wx = 0.4
    wy = 0.1
    window_height = 650
    window_width = 600
    opened_windows = Dict

    query_table = None
    record_klass = None
    query_klass = None

    limit = Int(200, enter_set=True, auto_set=False)
    date_str = 'Run Date/Time'

    add_query_button = Button('+')
    delete_query_button = Button('-')
    load_recent_button = Button('Load Recent')
    recent_days = Int(1)

    queries = List(Query)
    lookup = Dict
    style = Enum('normal', 'panel', 'simple', 'single')

    verbose = False

    selected_query = Any

    def __init__(self, *args, **kw):
        super(DatabaseSelector, self).__init__(*args, **kw)
        self._load_hook()

    def load_records(self, dbs, append=False):
        if not append:
            self.records = []

        self._load_records(dbs)
        #        self._sort_columns(self.records)
        if self.scroll_to_bottom:
            self.scroll_to_row = len(self.records) - 1
            #         self.debug('scb= {}, scroll to row={}'.format(self.scroll_to_bottom, self.scroll_to_row))

    def table_add_query(self):
        self._add_query(add=False)

    def query_factory(self, *args, **kw):
        return self._query_factory(**kw)

    def add_query(self, parent_query, parameter, comparator, criterion, add=True):
        q = self._query_factory(
            parent_parameters=parent_query.parent_parameters + [parameter],
            parent_criterions=parent_query.parent_criterions + [criterion],
            parent_comparators=parent_query.parent_comparators + [comparator],)
        if add:
            self.queries.append(q)
        parent_query.on_trait_change(q.update_parent_parameter, 'parameter')
        parent_query.on_trait_change(q.update_parent_criterion, 'criterion')
        parent_query.on_trait_change(q.update_parent_comparator, 'comparator')

    def remove_query(self, q):
        if q in self.queries:
            self.queries.remove(q)

    def load_recent(self, criterion='this month'):
        with self.db.session_ctx():
            # dbs = timethis(self._get_recent, args=(criterion, ))
            # timethis(self.load_records, args=(dbs, ), kwargs={'load':False})

            dbs = self._get_recent(criterion)
            self.load_records(dbs)

    def load_last(self, n=200):
        with self.db.session_ctx():
            dbs, _stmt = self._get_selector_records(limit=n)
            self.load_records(dbs)

            #    def execute_query(self, filter_str=None):

    def execute_query(self, queries=None, use_filters=True):
        with self.db.session_ctx():
            dbs = self._execute_query(queries, use_filters=use_filters)
            self.load_records(dbs)

    def get_last(self, n):
        dbs, _stmt = self._get_selector_records(limit=n)
        return dbs

    def get_recent(self, criterion='this month'):
        return self._get_recent(criterion)

    def get_date_range(self, start, end, **kw):
        qs = self.query_factory(criterion=start, parameter=self.date_str, comparator='>=')
        qe = self.query_factory(criterion=end, parameter=self.date_str, comparator='<=')
        return self._execute_query([qs, qe], **kw)

    #===============================================================================
    # private
    #===============================================================================
    def _add_query(self, add=True):
        pq = None
        if self.queries:
            pq = self.queries[-1]

        if pq is None:
            q = self._query_factory()
            if add:
                self.queries.append(q)
        else:
            self.add_query(pq, pq.parameter, pq.comparator, pq.criterion, add=add)

    def _get_recent(self, criterion):
        q = self.queries[0]
        q.parameter = self.date_str
        q.comparator = '>'
        q.trait_set(criterion=criterion)

        return self._execute_query(queries=[q])

    def _assemble_query(self, q, queries, lookup):
        joined = []
        for qi in queries:
            if not qi.use:
                continue

            if not qi.criterion:
                continue

            if lookup.has_key(qi.parameter):
                tabs, attr = lookup[qi.parameter]
                for tab in tabs:
                    if not tab in joined:
                        joined.append(tab)
                        q = q.join(tab)
                try:
                    q = qi.assemble_filter(q, attr)
                except ValueError:
                    self.warning_dialog('Invalid query "{}", "{}"'.format(qi.parameter, attr))
                    return

        return q

    def _execute_query(self, queries=None, limit=None, use_filters=True):
        if queries is None:
            queries = self.queries

        if limit is None:
            limit = self.limit
            # @todo: only get displayed columns

        dbs, query_str = self._get_selector_records(limit=limit,
                                                    queries=queries,
                                                    use_filters=use_filters)

        if not self.verbose:
            query_str = str(query_str)
            query_str = query_str.split('WHERE')[-1]
            query_str = query_str.split('ORDER BY')[0]

        self.info('query {} returned {} records'.format(query_str,
                                                        len(dbs) if dbs else 0))
        return dbs

    def _load_records(self, records):
        if records:
            '''
                using a IsotopeRecordView is significantly faster than loading a IsotopeRecord directly
            '''
            def func(x, prog, i, n):
                if prog:
                    prog.change_message('Loading {}/{} {}'.format(i+1, n, x.record_id))
                return self._record_view_factory(x)

            rs = progress_loader(records, func)
            self.records.extend(rs)

    def _record_closed(self, obj, name, old, new):
        sid = obj.record_id
        if sid in self.opened_windows:
            self.opened_windows.pop(sid)

        obj.on_trait_change(self._record_closed, 'close_event', remove=True)

    #        obj.on_trait_change(self._changed, '_changed', remove=True)

    def _record_view_factory(self, dbrecord):
        if hasattr(self, 'record_view_klass'):
            d = self.record_view_klass()
            if d.create(dbrecord, fast_load=True):
                return d
        else:
            return self.record_klass(_dbrecord=dbrecord)

            #===============================================================================
            # open window
            #===============================================================================

    def _open_selected(self, records=None):
        self.debug('open selected')
        if records is None:
            records = self.selected

        if records is not None:
            if isinstance(records, (list, tuple)):
                records = records[0]
            self._open_individual(records)

        self.debug('opened')

    def _open_individual(self, si):
        si = self._record_factory(si)

        if isinstance(si, str):
            si = self._record_factory(si)
        else:
            si.selector = self

        if not si.initialize():
            return

        sid = si.record_id
        try:
            si.load_graph()
            si.window_x = self.wx
            si.window_y = self.wy

            def do(si, sid):
            #                app = self.db.application
            #                from pyface.tasks.task_window_layout import TaskWindowLayout
            #                win = app.create_window(TaskWindowLayout('pychron.recall'))
            #                win.active_task.record = si
            #                print win.active_task.record
            #                win.open()
            #                self.debug('{}'.format(si))
                info = si.edit_traits()
                self._open_window(sid, info)

            self.debug('do later open')
            invoke_in_main_thread(do, si, sid)

        except Exception, e:
            import traceback

            traceback.print_exc()
            self.warning(e)

    def _open_window(self, wid, ui):
        self.opened_windows[wid] = ui
        self._update_windowxy()

        if self.db.application is not None:
            self.db.application.add_view(ui)

    def _update_windowxy(self):
        self.wx += 0.005
        self.wy += 0.03

        if self.wy > 0.65:
            self.wx = 0.4
            self.wy = 0.1

    def _get_selector_records(self):
        pass

    def _get_records(self, q, queries, limit, timestamp='timestamp'):
        if queries:
            q = self._assemble_query(q, queries, self.lookup)

        if q:
            tattr = getattr(self.query_table, timestamp)
            q = q.order_by(tattr.desc())
            if limit and limit > 0:
                q = q.limit(limit)

            q = q.from_self()
            q = q.order_by(tattr.asc())
            records = q.all()

            return records, compile_query(q)
        else:
            return [], 'invalid query'

    def _load_hook(self):
        pass

    def _get_num_records(self):
        return 'Number Results: {}'.format(len(self.records))

    #===============================================================================
    # handlers
    #===============================================================================
    def _load_recent_button_fired(self):
        criterion = 'this month'
        if self.recent_days:
            t = datetime.now()- timedelta(days=self.recent_days)
            criterion = t.strftime('%m/%d/%Y')
        self.load_recent(criterion=criterion)

    def _delete_query_button_fired(self):
        self.remove_query(self.selected_query)

    def _add_query_button_fired(self):
        self._add_query()

    def _dclicked_changed(self):
    #        self.debug('dclicked changed {}'.format(self.dclicked))
        if self.dclicked and self.dclick_recall_enabled:
            self._open_selected()

    # def _open_button_fired(self):
    #     self.debug('open button fired')
    #     self._open_selected()

    def _search_fired(self):
        self.execute_query()

    #        if self.records:
    #            self.selected = self.records[-1:]
    #            self.scroll_to_row = len(self.records) - 1
    #            print self.records.index(self.selected[0])

    def _limit_changed(self):
        self.execute_query()

    @on_trait_change('db.[name,host]')
    def _id_string_change(self):
        if self.db.kind == 'mysql':
            self.id_string = 'Database: {}:{}'.format(self.db.host,self.db.name)
        else:
            self.id_string = 'Database: {}'.format(self.db.name)

            #    def _selected_changed(self):
            #        if self.selected:
            #            sel = self.selected
            #            if self.style != 'single':
            #                sel = sel[0]
            #            self.selected_row = self.records.index(sel)
            #            self.update = True
            #===============================================================================
            # factories
            #===============================================================================

    def _query_factory(self, removable=True, **kw):
        q = self.query_klass(selector=self,
                             removable=removable,
                             date_str=self.date_str)

        q.trait_set(trait_change_notify=False, **kw)
        return q

    def _record_factory(self, di):
        di.on_trait_change(self._record_closed, 'close_event')
        return di

    #===============================================================================
    # views
    #===============================================================================
    def _get_button_grp(self):
        return HGroup(spring, Item('search', show_label=False), defined_when='style=="normal"')

    def panel_view(self):
        v = self._view_factory()
        return v

    def traits_view(self):
        v = self._view_factory()
        v.title = self.title
        v.width = self.window_width
        v.height = self.window_height
        v.x = 0.1
        v.y = 0.1

        return v

    def _view_factory(self):
        editor = myTabularEditor(adapter=self.tabular_adapter,
                                 dclicked='object.dclicked',
                                 selected='object.selected',
                                 selected_row='object.selected_row',
                                 update='update',
                                 scroll_to_row='scroll_to_row',
                                 #                               auto_update=True,
                                 column_clicked='object.column_clicked',
                                 editable=False,
                                 multi_select=not self.style == 'single')

        button_grp = self._get_button_grp()
        v = View(
            VGroup(
                CustomLabel('id_string', color='red'),
                VSplit(
                    Item('records',
                         style='custom',
                         editor=editor,
                         show_label=False,
                         height=0.75,
                         # width=600,
                    ),
                    Item('queries', show_label=False,
                         style='custom',
                         height=0.25,
                         editor=ListEditor(mutable=False,
                                           style='custom',
                                           editor=InstanceEditor()),
                         defined_when='style in ["normal","panel"]')),
                button_grp),
            resizable=True,
            handler=SelectorHandler)

        if self.style == 'single':
            v.buttons = ['OK', 'Cancel']
        return v

    #===============================================================================
    # defaults
    #===============================================================================
    def _queries_default(self):
        return [self._query_factory(removable=False)]

    def _tabular_adapter_default(self):
        return self.tabular_adapter_klass()

#============= EOF =============================================
#        if criteria is None:
#            criteria = self.criteria
#        self.criteria = criteria
#
#        db = self.db
#        if db is not None:
#
#            s = self._get_filter_str(param, comp, criteria)
#            if s is None:
#                return

#            kw = dict(filter_str=s,
#                      limit=self.limit,
#                      order=self._get_order()
#                      )
#            table, _ = param.split('.')
#            if not table == self.query_table.__tablename__:
#                kw['join_table'] = table

#            elif self.join_table:
#                kw['join_table'] = self.join_table
#                kw['filter_str'] = s + ' and {}.{}=="{}"'.format(self.join_table,
#                                                               self.join_table_col,
#                                                                        self.join_table_parameter
#                                                                        )
