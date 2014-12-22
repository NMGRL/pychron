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

from extraction_line_errors import *
from laser_errors import *


def _print_error_table(errors, loc):
#    for e in errors:
#        print e
    def get_code(x):
        try:
            v = loc[x]
            a = v(None, None, None, None)
            return a.code
        except TypeError, e:
            pass

    keys = sorted(errors, key=get_code)
    print '{:<30s} {}   {}'.format('Name', 'Code', 'Message')
    for k in keys:
        v = loc[k]
        a = v(None, None, None, None)
        if a.code is not None:
            print '{:<30s} {:03n}    {}'.format(k, int(a.code), a.msg)

def print_error_table():

    import extraction_line_errors
    import laser_errors

    errors = []
    loc = dict()
    for es in [extraction_line_errors, laser_errors]:
#    for es in [extraction_line_errors]:
#    for es in [laser_errors]:
        keys = [d for d in dir(es) if d.endswith('Code')]
        values = [getattr(es, k) for k in keys]

        errors += keys
        loc.update(dict(zip(keys, values)))
    print loc.keys()
    _print_error_table(errors, loc)

if __name__ == '__main__':
    print_error_table()
