# ===============================================================================
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
# ===============================================================================



import os

from datetime import datetime

from pychron.loggable import Loggable

MONTH_NAMES = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', \
               'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']


class DataWarehouse(Loggable):
    '''
        Class to construct data warehouses. A data warehouse is simple
        file directory with the following structure
        
        YEAR
            MONTH
                file.ext
                
                
    '''
    root = None
    _current_dir = None

    def get_current_dir(self):
        ''' 
        '''
        return self._current_dir

    def build_warehouse(self):
        r = self.root
        if r is None:
            return

        dirs = []
        if not os.path.isdir(r):

            head, tail = os.path.split(r)
#            print head, tail
            dirs.append(tail)
            while not os.path.isdir(head):
#                print head, tail
                head, tail = os.path.split(head)
                dirs.insert(0, tail)

            p = head
            for d in dirs:
                p = os.path.join(p, d)
                os.mkdir(p)

        # create subdirectory for this month
        self._current_dir = self._create_subdirectories()

    def _create_subdirectories(self):

        today = datetime.today()
        m = MONTH_NAMES[today.month - 1]
        y = today.year

        yd = self._create_subdir(self.root, y)
        md = self._create_subdir(yd, m)



        return md

    def _create_subdir(self, root, d):
        d = os.path.join(root, str(d))
        if not os.path.isdir(d):
            os.mkdir(d)

#        self._lock_path(d)
        return d

    def _lock_path(self, p):
        os.chown(p, 0, -1)
#        os.chmod(p, stat.S_IROTH | stat.S_IRGRP | stat.S_IREAD)

if __name__ == '__main__':
    d = DataWarehouse(root='/Users/ross/Sandbox/foo/moo')
    d.build_warehouse()






