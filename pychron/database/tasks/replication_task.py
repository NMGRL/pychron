# ===============================================================================
# Copyright 2014 Jake Ross
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
import os
from pychron.core.ui import set_qt
from pychron.paths import paths
from pychron.persistence_loggable import load_persistence_dict, load_persistence_values, dump_persistence_values

set_qt()

# ============= enthought library imports =======================
import time
from pyface.timer.do_later import do_after
from traits.api import HasTraits, Button, List, Int, on_trait_change
from traits.trait_types import Str, Password
from traitsui.api import View, Item
# ============= standard library imports ========================
import pymysql
# ============= local library imports  ==========================
from pychron.core.pychron_traits import IPAddress
from pychron.database.tasks.panes import SlavePane
from pychron.envisage.tasks.base_task import BaseTask


class StatusItem(HasTraits):
    display_name = Str
    tag = Str
    value = Str

    def __init__(self, display_name, tag, value, *args, **kw):
        super(StatusItem, self).__init__(*args, **kw)
        self.display_name = display_name
        self.tag = tag
        self.value = value


class ReplicationTask(BaseTask):
    check_status_button = Button
    host = IPAddress(enter_set=True, auto_set=False)
    user = Str(enter_set=True, auto_set=False)
    password = Password(enter_set=True, auto_set=False)
    skip_count = Int(1)

    skip_button = Button
    start_button = Button
    stop_button = Button

    last_error = Str
    status_items = List
    _connection = None

    def activated(self):
        self.host = 'localhost'
        self.user = 'root'
        self.password = 'Argon'
        self._load()
        self._check_status()

    def prepare_destroy(self):
        self._dump()
        if self._connection:
            self._connection.close()
            self._connection = None

    def create_central_pane(self):
        return SlavePane(model=self)

    def _load(self):
        p = os.path.join(paths.hidden_dir,'slave')
        load_persistence_values(self, p, ('host','user','password'))

    def _dump(self):
        p = os.path.join(paths.hidden_dir,'slave')
        dump_persistence_values(self, p, ('host','user','password'))

    def _get_connection(self):
        if not self._connection:
            try:
                con = pymysql.connect(host=self.host,
                                      port=3306,
                                      user=self.user,
                                      passwd=self.password)
                self._connection = con
            except pymysql.OperationalError, e:
                self.sql_warning(e)

        return self._connection

    def execute_sql(self, s, ret=None):
        """
            if ret=='cursor' return the Cursor object. remember to close it when finished
            with Cursor.close()
        """
        con = self._get_connection()
        if con:
            cur = con.cursor()
            try:
                cur.execute(s)
            except pymysql.InternalError, e:
                self.sql_warning(e)
                return

            if ret == 'cursor':
                return cur
            else:
                cur.close()

    def sql_warning(self, e):
        self.debug(e)
        self.warning_dialog('{}\nErrno: {}'.format(e[1], e[0]))

    def query_sql(self, s, query='all'):
        cur = self.execute_sql(s, ret='cursor')
        if cur:
            description = [di[0] for di in cur.description]
            if query == 'all':
                result = cur.fetchall()
            else:
                result = cur.fetchone()

            cur.close()
            return description, result

    def _check_status(self):
        """


        """
        r = self.query_sql('show slave status', query='one')
        running = False
        items = []
        last_error = ''
        if r:
            header, results = r
            nofunc = lambda x: x

            for args in (('Status', 'Slave_IO_State'),
                         ('MasterHost', 'Master_Host'),
                         ('IO Running', 'Slave_IO_Running'),
                         ('SQL Running', 'Slave_SQL_Running'),
                         ('Replicating DBs', 'Replicate_Do_DB'),
                         ('Seconds Behind', 'Seconds_Behind_Master', lambda x: '0' if x is None else x)):
                if len(args) == 2:
                    display_name, tag = args
                    func = nofunc

                else:
                    display_name, tag, func = args

                value = results[header.index(tag)]
                items.append(StatusItem(display_name, tag, func(value)))
            running = bool(items[0].value)
            last_error = results[header.index('Last_Error')]

        self.running = running
        self.status_items = items
        self.last_error = last_error

    def _start_slave(self):
        self.execute_sql('start slave')
        do_after(1000, self._check_status)

    def _check_status_button_fired(self):
        self._check_status()

    def _start_button_fired(self):
        self._start_slave()

    def _stop_button_fired(self):
        self.execute_sql('stop slave')
        do_after(1000, self._check_status)

    def _skip_button_fired(self):
        self.execute_sql('stop slave; SET GLOBAL sql_slave_skip_counter = {};'.format(self.skip_count))
        self._start_slave()

    @on_trait_change('host, user, password')
    def _handle_auth(self):
        if self._connection:
            self._connection.close()
            self._connection = None

            self._check_status()

if __name__ == '__main__':
    f = ReplicationTask()
    f.activated()
    sp = SlavePane(model=f)
    sp.configure_traits()
    f.prepare_destroy()

# ============= EOF =============================================



