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



import socket


import os


def server(kind, addr):
    if kind == 'inet':
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    else:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            os.remove(addr)
        except:
            print 'remove %s' % addr

    s.bind(addr)
    s.listen(1)
#    while 1:
    con, addr = s.accept()
    while 1:
        data = con.recv(1024)
        # print 'rec %s' % data
        if not data:break
        con.send(data)
    con.close()

if __name__ == '__main__':
    addr = '127.0.0.1', 1054
    addr = '/tmp/hardware'
    server('unix', addr)
