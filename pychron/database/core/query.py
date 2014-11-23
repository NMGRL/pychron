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

#============= enthought library imports =======================
from traits.api import HasTraits, String, Property, Str, List, Any, \
    Bool, cached_property, Event, Enum
from traitsui.api import View, Item, EnumEditor

#============= standard library imports ========================
from datetime import datetime, timedelta
from sqlalchemy import cast, Date
#============= local library imports  ==========================
now = datetime.now()
one_year = timedelta(days=365)


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

    txt = (comp % tuple(params)).decode(enc)
    return txt


class TableSelector(HasTraits):
    parameter = String
    parameters = Property

    def _get_parameters(self):
        params = [
            'Analysis',
            'Material',
            'Sample',
            'Detector',
            'IrradiationPosition', ]
        self.parameter = params[0]
        return params

    def traits_view(self):
        v = View(Item('parameter',
                      show_label=False,
                      editor=EnumEditor(name='parameters')),
                 buttons=['OK', 'Cancel'],
                 kind='livemodal')
        return v


class Query(HasTraits):
    use = Bool(True)
    parameter = String
    parameters = Property

    comparator = Str('=')
    comparisons = List(['=', '<', '>', '<=', '>=', 'not =',
                        'starts with',
                        'contains', 'between'])
    criterion = String('')
    criteria = Property(depends_on='parameter,criteria_dirty')
    criteria_dirty = Event

    selector = Any

    # add = Button('+')
    # remove = Button('-')

    chain_rule = Enum('', 'And', 'Or')
    #     removable = Bool(True)

    parent_parameters = List(String)
    parent_criterions = List(String)
    parent_comparators = List(String)

    is_last = Bool(False)

    def assemble_filter(self, query, attr):
        """
            query: sqlalchemy.Query object
            attr: sqlalchemy.Table.Column object

            modify the query object by chaining .filter calls

        """
        comp = self.comparator
        if self.parameter == 'Run Date/Time':
            ret = self.date_query(query, attr)
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
            ret = getattr(attr, comp)(c)

        print self.parameter, self.chain_rule
        return ret, self.chain_rule == 'Or'
        # if self.chain_rule=='Or':
        #     f = or_(f)
        # query = query.filter(f)

        # return query

    def _named_date_query(self, query, attr, comp, crit):
        today = datetime.today()
        if crit == 'this month':
            d = datetime.today()
            if '=' in comp:
                d, _ = self._convert_named_date(crit)
                return attr.between(today, d)
                # query = query.filter(attr.between(today, d))
                # return query

            else:
                dt = d - timedelta(days=d.day - 1)

        elif crit == 'this week':
            days = today.weekday()
            dt = timedelta(days=days)

        elif crit == 'yesterday':
            dt = today - timedelta(days=1)

        return getattr(attr, comp)(dt)
        # query = query.filter(getattr(attr, comp)(dt))
        # return query

    def _convert_named_date(self, c, comp=None):
        if c in ('this month', 'yesterday', 'this week'):
            fmt = ''
            today = datetime.today()
            if c == 'this month':
                d = datetime.today()
                if comp is None:
                    comp = self.comparator
                    comp = self._convert_comparator(comp)

                if '=' in comp:
                    ret = d - timedelta(days=d.day, seconds=d.second, hours=d.hour, minutes=d.minute)
                else:
                    ret = d - timedelta(days=d.day - 1)
            elif c == 'this week':
                days = today.weekday()
                ret = timedelta(days=days)
            elif c == 'yesterday':
                ret = today - timedelta(days=1)
        else:
            c = c.replace('/', '-')
            if c.count('-') == 2:
                y = c.split('-')[-1]
                y = 'y' if len(y) == 2 else 'Y'

                fmt = '%m-%d-%{}'.format(y)
            elif c.count('-') == 1:
                y = c.split('-')[-1]
                y = 'y' if len(y) == 2 else 'Y'

                fmt = '%m-%{}'.format(y)
            else:
                fmt = '%Y' if len(c) == 4 else '%y'

            ret = datetime.strptime(c, fmt)

        return ret, fmt

    def date_query(self, q, attr):
        criterion = self.criterion
        comp = self.comparator
        comp = self._convert_comparator(comp)
        # c = criterion.replace('/', '-')
        if criterion in ('this month', 'yesterday', 'this week'):
            return self._named_date_query(q, attr, comp, criterion)
        else:
            d, fmt = self._convert_named_date(criterion, comp)
            if comp == 'between':
                d = (d, datetime.strptime(self.rcriterion, fmt))
            else:
                d = (d, )

            attr = cast(attr, Date)
            # q = q.filter(getattr(attr, comp)(*d))
            return getattr(attr, comp)(*d)
            # return q

    #===============================================================================
    # private
    #===============================================================================
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

        return c

    def _get_parameters(self):
        params = self.__params__
        if not self.parameter:
            self.parameter = params[0]

        return params

    #===============================================================================
    # handlers
    #===============================================================================
    # def _add_fired(self):
    #     self.selector.add_query(self, self.parameter, self.criterion)
    #
    # def _remove_fired(self):
    #     self.selector.remove_query(self)

    def update_parent_parameter(self, obj, name, old, new):
        if old in self.parent_parameters:
            self.parent_parameters.remove(old)

        self.parent_parameters.append(new)
        self.criteria_dirty = True

    def update_parent_criterion(self, obj, name, old, new):
        if old in self.parent_criterions:
            self.parent_criterions.remove(old)

        self.parent_criterions.append(new)
        self.criteria_dirty = True

    def update_parent_comparator(self, obj, name, old, new):
        if old in self.parent_comparators:
            self.parent_comparators.remove(old)

        self.parent_comparators.append(new)
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
            ys = db.get_years_active()
            cs = ys + ['this month', 'yesterday', 'this week']
        else:
            kw = {}
            func = None
            display_name = 'name'

            def extract(ci, _):
                return ci[0]

            if param == 'irradiation':
                funcname = 'get_irradiations_join_analysis'
                func = extract
            elif param == 'labnumber':
                funcname = 'get_labnumbers_join_analysis'
                display_name = 'idenfifier'
                func = extract
            elif param == 'aliquot':
                display_name = 'aliquot'
            elif param == 'step':
                display_name = 'step'
            else:
                funcname = 'get_{}s'.format(param)

            if hasattr(db, funcname):
                if param == 'labnumber':
                    display_name = 'identifier'

                cj = self._cumulate_joins()
                cf = self._cumulate_filters()
                cs = getattr(db, funcname)(joins=cj,
                                           filters=cf, **kw)
                if func is None:
                    func = getattr
                # cs = list(set([getattr(ci, display_name) for ci in cs]))
                cs = [func(ci, display_name) for ci in cs]
                # cs.sort()
                cs = map(str, cs)
        return cs

    def _cumulate_joins(self):
        ps = self.parent_parameters  #+[self.parameter]
        if ps:
            tjs = []

            for pi in ps:
                if pi in self.selector.lookup:
                    js = self.selector.lookup[pi][0]
                    for ji in js:
                        if ji not in tjs:
                            tjs.append(ji)
            return tjs

    def _cumulate_filters(self):
        ps = self.parent_parameters  #+[self.parameter]
        pc = self.parent_comparators  #+[self.comparator]
        pr = self.parent_criterions  #+[self.criterion]
        if ps:
            tfs = []
            for pi, co, ci in zip(ps,
                                  pc,
                                  pr):

                co = self._convert_comparator(co)
                if pi == 'Run Date/Time':
                    ci, _ = self._convert_named_date(ci)

                if pi in self.selector.lookup:
                    fi = self.selector.lookup[pi][1]
                    if co is None:
                        f = fi == ci
                    else:
                        f = getattr(fi, co)(ci)

                    tfs.append(f)
            return tfs

            #===============================================================================
            # views
            #===============================================================================

            # def traits_view(self):
            #
            #     top = HGroup(
            #
            #         Item('parameter', editor=EnumEditor(name='parameters')),
            #         Item('comparator',
            #              editor=EnumEditor(name='comparisons')),
            #         show_labels=False)
            #
            #     bottom = HGroup(
            #         Item('add', ),
            #         Item('remove',
            #              visible_when='removable'),
            #         Item('criterion', ),
            #         Item('criterion', width=-30,
            #              editor=CheckListEditor(name='criteria')),
            #         Item('rcriterion', visible_when='comparator=="between"'),
            #         Item('rcriterion', width=-30,
            #              visible_when='comparator=="between"',
            #              editor=CheckListEditor(name='criteria')),
            #         show_labels=False)
            #
            #     v = View(VGroup(top, bottom,
            #                     show_border=True))
            #     return vs


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
