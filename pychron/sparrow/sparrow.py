# ===============================================================================
# Copyright 2019 ross
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
import json

import psycopg2
from apptools.preferences.preference_binding import bind_preference
from traits.api import Str, Int

from pychron.loggable import Loggable

CRS = 4326


def connect(**kw):
    dsn = "host='{host:}' user='{username:}' " \
          "dbname='{name:}' port='{port:}'".format(**kw)

    try:
        with psycopg2.connect(dsn) as conn:
            with conn.cursor() as cursor:
                    cursor.execute('select * from public.sample')
                    return True
    except BaseException as e:
        print(e)


class Sparrow(Loggable):
    dbname = Str
    username = Str
    password = Str
    host = Str
    port = Int

    _conn = None

    def __init__(self, bind=True, *args, **kw):
        super().__init__(*args, **kw)
        if bind:
            self.bind_preferences()

    def connect(self):
        return connect(name=self.dbname, host=self.host, username=self.username, port=self.port, password=self.password)

    def bind_preferences(self):
        prefid = 'pychron.sparrow'
        for attr in ('dbname', 'username', 'password', 'host', 'port'):
            bind_preference(self, attr, '{}.{}'.format(prefid, attr))

    def insert_ia(self, path):
        with open(path, 'r') as rfile:
            obj = json.load(rfile)

        sm = obj.get('sample_metadata')
        cm = obj.get('collection_metadata')
        ans = obj.get('analyses')
        pf = obj.get('preferred')

        sm['crs'] = CRS
        with self._connection() as conn:
            self._conn = conn

            self._insert_default_parameters()
            self._insert_project(sm)
            self._insert_material(sm)
            self._insert_sample(sm)

            instr_id = self._insert_instrument(cm['instrument'])
            session_id = self._insert_session(sm['sample'], sm['project'], instr_id, cm['technique'])

            self._insert_analyses(session_id, ans, sm)
            self._insert_preferred(session_id, pf, sm)

    # private
    def _insert_default_parameters(self):
        authority = 'NMGRL'
        sql = '''insert into vocabulary.unit (id, authority)
        values (%s, %s)'''

        self._insert(sql, ('dimensionless', authority))
        self._insert(sql, ('fA', authority))
        self._insert(sql, ('W', authority))
        self._insert(sql, ('1/a', authority))

        sql = '''insert into vocabulary.parameter (id, description, authority)
        values (%s, %s, %s)'''
        self._insert(sql, ('Extract_Value', '', authority))
        self._insert(sql, ('Monitor_Age', '', authority))
        self._insert(sql, ('K40_Lambda', '', authority))
        self._insert(sql, ('Ar40_RGY', '', authority))
        self._insert(sql, ('KCa', '', authority))
        self._insert(sql, ('KCl', '', authority))

    def _insert_preferred(self, session_id, pf, sm):
        aid = self._insert_analysis(session_id, sm, is_interpreted=True)
        for obj, attrs in ((pf, (('age', 'Age', pf['display_age_units']),
                                 ('monitor_age', 'Monitor_Age', 'Ma'),
                                 ('mswd', 'MSWD', 'dimensionless'))),
                           (pf['arar_constants']), (('lambda_k', 'K40_Lambda', '1/a'),
                                                    ('atm4036', 'Ar40_Ar36', 'dimensionless'))):
            for attr, param, unit in attrs:
                mtype = self._insert_datum_type(param, unit, is_interpreted=True)
                self._insert_datum(aid, mtype, obj.get(attr), obj.get('{}_err'.format(attr)))

    def _insert_analyses(self, session_id, ans, sm):
        types = (('age', 'Age', 'Ma'),
                 ('radiogenic_yield', 'Ar40_RGY', '%'),
                 ('f', 'Ar40RG_Ar39K', 'dimensionless'),
                 ('kca', 'KCl', 'dimensionless'),
                 ('kcl', 'KCl', 'dimensionless'))

        types = {attr: self._insert_datum_type(param, unit) for attr, param, unit in types}

        keys = ['Ar40', 'Ar39', 'Ar38', 'Ar36']
        signal_types = {k: self._insert_datum_type(k, 'fA') for k in keys}

        for i, a in enumerate(ans):
            timestamp = a.get('timestamp')
            analysis_id = self._insert_analysis(session_id, sm, idx=i + 1, date=timestamp)

            ev_type = self._insert_datum_type('Extract_Value', a.get('extract_units', 'W'))
            self._insert_datum_type(analysis_id, ev_type, a['extract_value'])

            is_bad = a.get('tag') != 'ok'
            for attr, dtype in types.items():
                value = a.get(attr, 0)
                error = a.get('{}_err'.format(attr), 0)
                self._insert_datum(analysis_id, dtype, value, error, is_bad)

            ifc = a['interference_corrected_values']
            for k in keys:
                v = ifc[k]
                self._insert_datum(analysis_id,
                                   signal_types[k],
                                   v.get('value', 0), v.get('error', 0), is_bad)

    def _insert_instrument(self, instr):
        sql = '''insert into public.instrument (name)
                            values (%s)'''
        self._insert(sql, (instr,))

        with self._conn.cursor() as cursor:
            sql = 'select * from public.instrument where name=%s'
            cursor.execute(sql, (instr,))
            return cursor.fetchone()[0]

    def _insert_material(self, sm):
        sql = '''insert into vocabulary.material (id)
                    values (%(material)s)'''
        self._insert(sql, sm)

    def _insert_project(self, sm):
        sql = '''insert into public.project (id, title)
            values (%(project)s, %(project)s)'''
        self._insert(sql, sm)

    def _insert_sample(self, sm):
        sql = '''insert into public.sample (id, material, location) 
            values (%(sample)s, %(material)s, ST_SetSRID(ST_Point(%(longitude)s,%(latitude)s),%(crs)s))'''
        self._insert(sql, sm)

    def _insert_session(self, sample, project, instrument, technique):
        sql = '''insert into public.session (sample_id, project_id, date, instrument, technique)
            values (%s, %s, now(), %s, %s)'''

        self._insert(sql, (sample, project, instrument, technique))
        return self._get_last_id('session')

    def _insert_datum(self, aid, dtype, value, error=0, is_bad=None):
        sql = '''insert into public.datum (analysis, type, value, error, is_bad)
                    values (%s,%s,%s,%s,%s)'''
        datum = (aid, dtype, value, error, is_bad)
        self._insert(sql, datum)

    def _insert_datum_type(self, parameter, unit, is_interpreted=False):
        asql = 'select * from public.datum_type where parameter=%s and unit=%s and is_interpreted=%s'
        atype = self._get_one(asql, (parameter, unit, is_interpreted))

        if atype is None:
            sql = '''insert into public.datum_type (parameter, unit, is_interpreted)
            values (%s,%s,%s)'''
            self._insert(sql, (parameter, unit, is_interpreted))

            atype = self._get_one(asql, (parameter, unit, is_interpreted))

        return atype

    def _insert_analysis(self, session_id, sm, idx=0, date=None, is_interpreted=False):
        sql = '''insert into public.analysis (session_id, session_index, analysis_type, date, material, is_interpreted)
                    values (%(session_id)s, 
                    %(session_idx)s, 
                    %(analysis_type)s, 
                    %(date)s,
                    %(material)s,
                    %(is_interpreted)s)'''

        d = {'session_id': session_id, 'session_idx': idx,
             'analysis_type': '',
             'date': date,
             'material': sm['material'],
             'is_interpreted': is_interpreted}

        self._insert(sql, d)

        return self._get_last_id('analysis')

    def _get_one(self, sql, var=None, default=None):
        with self._conn.cursor() as cursor:
            cursor.execute(sql, var)
            try:
                return cursor.fetchone()[0]
            except TypeError:
                return default

    def _get_last_id(self, table):
        sql = 'select * from public.{} order by id desc'.format(table)
        return self._get_one(sql)

    def _insert(self, sql, sm, verbose=False):
        with self._conn.cursor() as cursor:
            try:
                cursor.execute(sql, sm)
                self._conn.commit()
            except psycopg2.IntegrityError as e:
                if verbose:
                    print(e)

                self._conn.rollback()
                return

    def _connection(self):
        dsn = "host='{host:}' user='{user:}' " \
              "dbname='{name:}' port='{port:}'".format(name=self.dbname, user=self.user,
                                                       host=self.host, port=self.port)

        return psycopg2.connect(dsn)


if __name__ == '__main__':
    s = Sparrow(dbname='sparrow', user='postgres',
                host='localhost',
                port=54321, bind=False)
    p = '/Users/ross/Desktop/14_00000.ia.json'
    s.insert_ia(p)
# ============= EOF =============================================
