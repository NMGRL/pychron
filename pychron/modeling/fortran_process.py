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

#=============enthought library imports=======================
from traits.api import  Str
# from pyface.timer.do_later import do_later
from pyface.message_dialog import warning
#============= standard library imports ========================
from threading import Thread
import subprocess
import os
import sys
import time

#============= local library imports  ==========================
from pychron.loggable import Loggable
# from pychron.progress_dialog import myProgressDialog

class FortranProcess(Loggable):
    _thread = None
    _process = None
    name = Str
    root = Str
    rid = Str
    state = Str
    def __init__(self, name, root, rid, queue=None, *args, **kw):
        super(FortranProcess, self).__init__(*args, **kw)
#        Thread.__init__(self)
        self.name = name
        self.root = root
        self.success = False
        self.rid = rid
        delimiter = ':'
        if sys.platform != 'darwin':
            delimiter = ';'

        ps = os.environ['PATH'].split(delimiter)
        if not root in ps:
            os.environ['PATH'] += '{}{}'.format(delimiter, root)

        self.queue = queue

    def start(self):
        self._thread = Thread(target=self._run)
        self._thread.start()

    def isAlive(self):
        if self._thread:
            return self._thread.isAlive()

    def _run(self):
        p = os.path.join(self.root, self.name)
        if not os.path.exists(p):
            warning(None, 'Invalid Clovera path {}'.format(self.root))
            return

#        n = 5
#        pd = myProgressDialog(max=n, size=(550, 15))
#        do_later(pd.open)
#        do_later(pd.change_message, '{} process started'.format(self.name))
        try:
            p = subprocess.Popen([p],
                                  shell=False,
                                  bufsize=1024,
                                  stdout=subprocess.PIPE
                                  )
            self._process = p
            while p.poll() == None:
                if self.queue:
                    self.queue.put(p.stdout.readline())
                time.sleep(1e-6)

            self.success = True
#            do_later(pd.change_message, '{} process complete'.format(self.name))

            return True

        except OSError, e:
            self.warning_dialog('Clovera programs are not executable. Check Default Clovera Directory.\n{}'.format(e))
            import traceback
            traceback.print_exc()
            # warning(None, '{} - {}'.format(e, self.name))
#            do_later(pd.change_message, '{} process did not finish properly'.format(self.name))

    def get_remaining_stdout(self):
        if self._process:
            try:
                txt = self._process.communicate()[0]
                if txt:
                    return txt.split('\n')
            except Exception, e:
                pass
                # print 'get remaining stdout',e
        return []



if __name__ == '__main__':
    import Queue
    q = Queue.Queue()
    d = '/Users/Ross/Desktop'
    f = FortranProcess('hello_world', d, q)
    print os.getcwd()
    os.chdir(d)
    f.start()
    time.clock()
    while f.isAlive() or not q.empty():
        l = q.get().rstrip()
        # print l

    # print f.get_remaining_stdout()
    print time.clock()
#============= EOF =====================================

