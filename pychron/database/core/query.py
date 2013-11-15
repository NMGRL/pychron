#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from datetime import datetime, timedelta

from traits.api import HasTraits, String, Property, Str, List, Button, Any, \
    Bool, cached_property, Event
from traitsui.api import View, Item, EnumEditor, HGroup, CheckListEditor, \
    VGroup
from sqlalchemy.sql.expression import and_

#============= standard library imports ========================
#============= local library imports  ==========================
class NItem(Item):
    pass
    padding = -15


def compile_query(query):
    from sqlalchemy.sql import compiler
    #    try:
    #        from MySQLdb.converters import conversions, escape
    #    except ImportError:
    #        return 'no sql conversion available'

    dialect = query.session.bind.dialect
    statement = query.statement
    comp = compiler.SQLCompiler(dialect, statement)
    enc = dialect.encoding
    params = []
    for k in comp.positiontup:
        v = comp.params[k]
        if isinstance(v, unicode):
            v = v.encode(enc)
        params.append(v)
        #        params.append(
    #                      escape(v, conversions)
    #                      )

    comp = comp.string.encode(enc)
    comp = comp.replace('?', '%s')

    return (comp % tuple(params)).decode(enc)


class TableSelector(HasTraits):
    parameter = String
    parameters = Property

    def _get_parameters(self):
        params = [
            'Analysis',
            'Material',
            'Sample',
            'Detector',
            'IrradiationPosition',
        ]
        self.parameter = params[0]
        return params

    def traits_view(self):
        v = View(Item('parameter',
                      show_label=False,
                      editor=EnumEditor(name='parameters')),
                 buttons=['OK', 'Cancel'],
                 kind='livemodal'
        )
        return v


class Query(HasTraits):
    use = Bool(True)
    parameter = String
    #    parameters = Property(depends_on='query_table')
    parameters = Property

    comparator = Str('=')
    comparisons = List(['=', '<', '>', '<=', '>=', 'not =',
                        'starts with',
                        'contains'
    ])
    criterion = String('')
    #    criterion = String('')
    criteria = Property(depends_on='parameter,criteria_dirty')
    criteria_dirty = Event
    #    query_table = Any

    selector = Any

    add = Button('+')
    remove = Button('-')
    #     removable = Bool(True)

    parent_parameters = List(String)
    parent_criterions = List(String)
    #    date_str = 'rundate'

    def assemble_filter(self, query, attr):
        comp = self.comparator
        if self.parameter == 'Run Date/Time':
            query = self.date_query(query, attr)
        else:
            c = self.criterion
            if comp in ['starts with', 'contains']:
                if comp == 'starts with':
                    comp = 'like'
                    c += '%'
                elif comp == 'contains':
                    comp = 'like'
                    c = '%' + c + '%'

            comp = self._convert_comparator(comp)
            query = query.filter(getattr(attr, comp)(c))

        return query

    def _named_date_query(self, query, attr, comp, crit):
        today = datetime.today()
        if crit == 'this month':
            d = datetime.today()
            if '=' in comp:
                d = d - timedelta(days=d.day, seconds=d.second, hours=d.hour, minutes=d.minute)
                query = query.filter(and_(attr <= today,
                                          attr >= d))
                return query

            else:
                dt = d - timedelta(days=d.day - 1)

        elif crit == 'this week':
            days = today.weekday()
            dt = timedelta(days=days)

        elif crit == 'yesterday':
            dt = today - timedelta(days=1)

        query = query.filter(getattr(attr, comp)(dt))
        return query

    def date_query(self, query, attr):
        criterion = self.criterion
        comp = self.comparator
        comp = self._convert_comparator(comp)
        c = criterion.replace('/', '-')
        if c in ('this month', 'yesterday', 'this week'):
            return self._named_date_query(query, attr, comp, c)
        else:

            if c.count('-') == 2:
                fmt = '%m-%d-%Y'
            elif c.count('-') == 1:
                fmt = '%m-%Y'
            else:
                fmt = '%Y'
            d = datetime.strptime(c, fmt)
            print attr, comp, c, d
            query = query.filter(getattr(attr, comp)(d))
            #        c = '{}'.format(c)
        return query

    #
    #===============================================================================
    # private
    #===============================================================================
    #    def _between(self, p, l, g):
    #        return '{}<="{}" AND {}>="{}"'.format(p, l, p, g)

    def _convert_comparator(self, c):
        if c == '=':
            c = '__eq__'
        elif c == '<':
            c = '__lt__'
        elif c == '>':
            c = '__gt__'
        elif c == '<=':
            c = '__le__'
        elif c == '>=':
            c = '__ge__'
            #        elif c=='like':

        return c

    #    @cached_property
    def _get_parameters(self):

    #        b = self.query_table
    #        params = [str(fi.column).split('.')[0].replace('Table', '').lower() for fi in b.__table__.foreign_keys]
    #
    #        params += [str(col) for col in b.__table__.columns]
    # #        f = lambda x:[str(col)
    # #                           for col in x.__table__.columns]
    # #        params = list(f(b))
        params = self.__params__
        if not self.parameter:
            self.parameter = params[0]

        return params

    #===============================================================================
    # handlers
    #===============================================================================
    def _add_fired(self):
        self.selector.add_query(self, self.parameter, self.criterion)

    def _remove_fired(self):
        self.selector.remove_query(self)

    def _update_parent_parameter(self, obj, name, old, new):
        if old in self.parent_parameters:
            self.parent_parameters.remove(old)

        self.parent_parameters.append(new)
        self.criteria_dirty = True

    def _update_parent_criterion(self, obj, name, old, new):
        if old in self.parent_criterions:
            self.parent_criterions.remove(old)

        self.parent_criterions.append(new)
        self.criteria_dirty = True

    #===============================================================================
    # property get/set
    #===============================================================================
    @cached_property
    def _get_criteria(self):
        cs = []
        db = self.selector.db
        param = self.parameter.lower()
        if param == 'run date/time':
            cs = ['2013', '2012', 'this month', 'yesterday', 'this week']
        else:
            funcname = 'get_{}s'.format(param)
            if hasattr(db, funcname):
                display_name = 'name'
                if param == 'labnumber':
                    display_name = 'identifier'
                elif param == 'aliquot':
                    display_name = 'aliquot'
                elif param == 'step':
                    display_name = 'step'

                cs = getattr(db, funcname)(joins=self._cumulate_joins(),
                                           filters=self._cumulate_filters())
                cs = list(set([getattr(ci, display_name) for ci in cs]))
                cs.sort()
                cs = map(str, cs)
        return cs

    def _cumulate_joins(self):
        if self.parent_parameters:
            tjs = []
            for pi in self.parent_parameters:
                if pi in self.selector.lookup:
                    js = self.selector.lookup[pi][0]
                    for ji in js:
                        if ji not in tjs:
                            tjs.append(ji)
            return tjs

    def _cumulate_filters(self):
        if self.parent_parameters:
            tfs = []
            for pi, ci in zip(self.parent_parameters, self.parent_criterions):
                if pi in self.selector.lookup:
                    fi = self.selector.lookup[pi][1]
                    tfs.append(fi == ci)
            return tfs

            #===============================================================================
            # views
            #===============================================================================

    def traits_view(self):

        top = HGroup(

            NItem('parameter', editor=EnumEditor(name='parameters'),
                  #                     width= -100
            ),
            #                Spring(springy=False,
            #                       width= -5),
            NItem('comparator',
                  editor=EnumEditor(name='comparisons'),
            ),
            #                NItem('add'),
            #                Spring(springy=False,
            #                       width=50, visible_when='not removable'),
            show_labels=False,

        )

        bottom = HGroup(
            NItem('add',
            ),
            NItem('remove',
                  visible_when='removable'),
            NItem('criterion',
            ),
            NItem('criterion', width=-30,
                  editor=CheckListEditor(name='criteria')),
            show_labels=False
        )

        v = View(VGroup(top, bottom,
                        show_border=True
        ))
        return v


class IsotopeQuery(Query):
    __params__ = [
        'Irradiation',
        'Labnumber',
        'Run Date/Time',
        'Irradiation Level',
        'Irradiation Position',
        'Sample',
        'Project',
        'Experiment',
        'Aliquot',
        'Step'
    ]


class DateQuery(Query):
    __params__ = ['Run Date/Time', ]


class DeviceScanQuery(DateQuery):
    pass


class PowerRecordQuery(DateQuery):
    pass


class PowerCalibrationQuery(DateQuery):
    pass


class PowerMapQuery(DateQuery):
    pass


class VideoQuery(DateQuery):
    pass


class BakeoutQuery(Query):
    __params__ = ['Run Date/Time',
                  'Controller'
    ]

#============= EOF =============================================
#        elif 'runtime' in param:
#    def time_query(self):
#        args = criteria.split(':')
#        if len(args) in [1, 2] and comp == '=':
#            base = ['00', ] * (3 - len(args))
#            g = ':'.join(args + base)
#            try:
#                a = [int(ai) + (1 if len(args) - 1 == i else 0)
#                    for i, ai in enumerate(args)]
#            except ValueError:
#                return None
#
#            f = ':'.join(['{:n}', ] * (len(args)) + base)
#            l = f.format(*a)
#            c = self._between(param , l, g)
#            return c
#        else:
#            c = ':'.join(args + ['00', ] * (3 - len(args)))
#    def get_filter_str(self,):
#        return self._get_filter_str(self.parameter, self.comparator, self.criterion)
#
#    def _get_filter_str(self, param, comp, criteria):
#        if self.date_str in param:
#            c = criteria.replace('/', '-')
#            if criteria == 'today':
#                c = get_date()
#            elif criteria == 'this month':
#                d = datetime.today().date()
#                today = get_date()
#                if '=' in comp:
#                    d = d - timedelta(days=d.day)
#                    c = self._between(param, today, d)
#                    return c
#                else:
#                    c = d - timedelta(days=d.day - 1)
#            c = '{}'.format(c)
#        elif 'runtime' in param:
#            args = criteria.split(':')
#            if len(args) in [1, 2] and comp == '=':
#                base = ['00', ] * (3 - len(args))
#                g = ':'.join(args + base)
#                try:
#                    a = [int(ai) + (1 if len(args) - 1 == i else 0)
#                        for i, ai in enumerate(args)]
#                except ValueError:
#                    return None
#
#                f = ':'.join(['{:n}', ] * (len(args)) + base)
#                l = f.format(*a)
#                c = self._between(param , l, g)
#                return c
#            else:
#                c = ':'.join(args + ['00', ] * (3 - len(args)))
#        else:
#            #convert forgein key param
#            if not '.' in param:
#                param = '{}.id'.format(param)
#
#            c = criteria
#
#        if comp == 'like':
#            c += '%'
#        elif comp == 'contains':
#            comp = 'like'
#            c = '%' + c + '%'
#
#        c = '"{}"'.format(c)
#        return ' '.join((param, comp, c))
