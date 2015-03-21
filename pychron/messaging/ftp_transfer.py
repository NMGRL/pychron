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



from __future__ import with_statement
# ============= enthought library imports =======================
# from traits.api import HasTraits, on_trait_change,Str,Int,Float,Button
# from traitsui.api import View,Item,Group,HGroup,VGroup

# ============= standard library imports ========================
import ftplib
import os

# ============= local library imports  ==========================
class FTPTranfer(object):
    '''
        G{classtree}
    '''
    _ftp = None
    def __init__(self, host, *args, **kw):
        '''
            @type host: C{str}
            @param host:

            @type *args: C{str}
            @param *args:

            @type **kw: C{str}
            @param **kw:
        '''
        self._connect(host)

    def transfer(self, path, name=None):
        '''
            @type path: C{str}
            @param path:

            @type name: C{str}
            @param name:
        '''
        if name is None:
            name = os.path.basename(path)
        if self._ftp is not None:
            self._ftp.cwd('argusVI_one_data')
            with open(path, 'r') as f:
                self._ftp.storlines('STOR %s' % name, f,
                                callback=self._transfer_line,
                                )

    def _transfer_line(self, args):
        '''
            @type args: C{str}
            @param args:
        '''
        print 'transfering %s' % args

    def _connect(self, host):
        '''
            @type host: C{str}
            @param host:
        '''
        self._ftp = f = ftplib.FTP(host)
        f.login(user='ross', passwd='jir812')

if __name__ == '__main__':
    f = FTPTranfer('localhost')
#    f._ftp.mkd('argusVI_one_data')
    p = '/Users/Ross/Desktop/airshot_script.txt'
    f.transfer(p)
# ============= EOF ====================================
