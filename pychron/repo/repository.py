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
#===============================================================================

#============= enthought library imports =======================
from traits.api import Str, Password, Property
#============= standard library imports ========================
import os
import ftplib as ftp
#============= local library imports  ==========================
from pychron.loggable import Loggable
import shutil
from zipfile import ZipFile, ZIP_DEFLATED
from pychron.core.helpers.filetools import unique_path


class Repository(Loggable):
    root = Str

    @property
    def name(self):
        return os.path.basename(self.root)

    @property
    def url(self):
        return self.root

    def connect(self):
        return True

    def add_file(self, p):
        pass

    #        pychron = p
    #        dst = self.get_file_path(p)
    #        shutil.copyfile(pychron, dst)

    def get_file_path(self, p):
        dst = os.path.join(self.root, os.path.basename(p))
        return dst

    def isfile(self, n):
        return os.path.isfile(self.get_file_path(n))

    def retrieveFile(self, n, out):
        try:
            shutil.copyfile(self.get_file_path(n), out)
            return True
        except Exception, e:
            print 'Repository retrievie file exception- ', e

    def compress(self, base='archive'):
        up, _cnt = unique_path(os.path.dirname(self.root), base, extension='zip')
        name = os.path.basename(up)
        with ZipFile(up, 'w', compression=ZIP_DEFLATED) as af:
            for p in os.listdir(self.root):
                if p.startswith('.'):
                    continue
                if p == name:
                    continue
                af.write(os.path.join(self.root, p), p)
        return name


class ZIPRepository(Repository):
    def retrieveFile(self, n, out):


        n = os.path.basename(n)
        with ZipFile(self.root, 'r') as zp:
            try:
                zp.extract(n, os.path.dirname(out))
                return True
            except Exception, e:
                print 'ZIPRepository retrievie file exception- ', e


class RemoteRepository(Repository):
    host = Str
    username = Str
    password = Password
    local_root = Str
    def open_repo(self, p):
        self.local_root=p

    def push(self):
        pass

    @property
    def path(self):
        return self.local_root

import paramiko


class SFTPRepository(RemoteRepository):
    client = Property(depends_on='host, username, password')
    _client = None
    _server_root = None

    def _get_client(self):
        if self._client is not None:
            return self._client

        t = paramiko.Transport((self.host, 22))
        t.connect(username=self.username,
                  password=self.password)

        sftp = paramiko.SFTPClient.from_transport(t)
        self._client = sftp
        return self._client

    def connect(self):
        return self.client

    def add_file(self, p):

        def cb(clt):
            bp = os.path.basename(p)
            self.info('adding {} to {}'.format(bp, clt.getcwd()))
            clt.put(p, bp)

        self._execute(cb)

    def isfile(self, n):
        def cb(clt):
            return n in clt.listdir()

        self._execute(cb)

    def _execute(self, cb):
        client = self.client
        if self._server_root is None:
            self._server_root = client.getcwd()

        if not client.getcwd() == os.path.join(self._server_root, self.root):
            client.chdir(self.root)

        return cb(client)

    #        return os.path.isfile(self.get_file_path(n))

    def retrieveFile(self, n, out):
        print n, out

        def cb(clt):
            clt.get(n, out)

        self._execute(cb)


class FTPRepository(Repository):
    #    def __init__(self, *args, **kw):
    #        self.root = root
    #        super(FTPRepository, self).__init__(*args, **kw)
    #    client = Property(depends_on='host, username, password')
    #    _client = None

    @property
    def url(self):
        return '{}@{}/{}'.format(self.username,
                                 self.host,
                                 self.root
        )

    def connect(self):
        c, _ = self.client
        return c is not None

    def _get_client(self):
        if self._client is not None:
            return self._client, None

        h = self.host
        u = self.username
        p = self.password
        if h is None:
            h = 'localhost'
        fc = None
        e = None

        #        print h, u, p
        try:
            fc = ftp.FTP(h, user=u,
                         passwd=p,
                         timeout=20)
            self._client = fc
        except Exception, e:
            pass

        return fc, e

    #    def get_file_path(self, cp):
    #        return os.path.join(self.root, cp)

    def retrieveFile(self, p, out):

        cb = lambda ftp: self._retreive_binary(ftp, p, out)
        self._execute(cb)

    def add_file(self, p):
        cb = lambda ftp: self._add_binary(ftp, p)
        return self._execute(cb)

    def isfile(self, cp):
        #        cp = self.get_file_path(cp)
        cb = lambda ftp: self._isfile(ftp, cp)
        return self._execute(cb)

    def _isfile(self, ftp, cp):
        #        ftp.cwd(self.root)
        return cp in ftp.nlst()

    def _retreive_binary(self, ftp, p, op):
        #        ftp.cwd(self.root)

        cb = open(op, 'wb').write
        ftp.retrbinary('RETR {}'.format(p), cb)

    def _add_binary(self, ftp, p, dst=None):
        #        ftp.cwd(self.root)
        if dst is None:
            dst = os.path.basename(p)
        with open(p, 'rb') as fp:
            ftp.storbinary('STOR {}'.format(dst), fp)

    def _add_ascii(self, ftp, p, dst=None):
        #        ftp.cwd(self.root)
        if dst is None:
            dst = os.path.basename(p)
        with open(p, 'r') as fp:
            ftp.storascii('STOR {}'.format(dst), fp)

    def _execute(self, cb):
        i = 0
        ntries = 3
        while i < ntries:
            i += 1
            ftp, err = self._get_client()
            if ftp is not None:
                print ftp
                #                print ftp.pwd(), os.path.join(self._server_root, self.root)
                ftp.cwd(self.root)
                return cb(ftp)
            #                try:
            #                    if self._server_root is None:
            #                        self._server_root = ftp.pwd()
            #                    if not ftp.pwd() == os.path.join(self._server_root, self.root):
            #                        ftp.cwd(self.root)
            #                    return cb(ftp)
            #                except Exception, e:
            #                    '''
            #                        clears the client property cache
            #                    '''
            # #                    self.reset = True
            #                    self._client = None
            #                    self.warning('execute exception {}'.format(e))
            else:
                print err


if __name__ == '__main__':
    c = FTPRepository(
        remote='Sandbox/ftp/data',
        #                      root='/',
        user='ross',
        password='jir812'
    )

    p = '/Users/ross/Sandbox/download.h5'
    c.add_file(p)

#============= EOF =============================================
