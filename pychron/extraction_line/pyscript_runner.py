# ===============================================================================
# Copyright 2011 Jake Ross
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

# ============= enthought library imports =======================
from traits.api import Any, Dict, List, provides
# ============= standard library imports ========================
from threading import Event, Lock
# ============= local library imports  ==========================
from pychron.core.helpers.logger_setup import logging_setup
from pychron.extraction_line.ipyscript_runner import IPyScriptRunner
from pychron.loggable import Loggable
from pychron.hardware.core.communicators.ethernet_communicator import EthernetCommunicator


@provides(IPyScriptRunner)
class PyScriptRunner(Loggable):
    resources = Dict
    _resource_lock = Any
    scripts = List

    def reset_connection(self):
        pass

    def connect(self):
        return True

    def __resource_lock_default(self):
        return Lock()

    def get_resource(self, name):
        with self._resource_lock:
            if name not in self.resources:
                self.resources[name] = self._get_resource(name)

            r = self.resources[name]
            return r

    def _get_resource(self, name):
        return Event()

        # def traits_view(self):
        #
        # cols = [ObjectColumn(name='logger_name', label='Name',
        #                           editable=False, width=150),
        #             CheckboxColumn(name='cancel_flag', label='Cancel',
        #                            width=50),
        #           ]
        #     v = View(Item('scripts', editor=TableEditor(columns=cols,
        #                                                 auto_size=False),
        #                   show_label=False
        #                   ),
        #              width=500,
        #              height=500,
        #              resizable=True,
        #              # handler=self.handler_klass(),
        #              title='ScriptRunner'
        #              )
        #     return v


class RemoteResource(object):
    handle = None
    name = None

    # ===============================================================================
    # threading.Event interface
    # ===============================================================================
    def read(self, verbose=True):
        resp = self.handle.ask('Read {}'.format(self.name), verbose=verbose)
        if resp is not None:
            return float(resp)

    def get(self):
        resp = self.read()
        return resp

    def isSet(self):
        resp = self.read()
        if resp is not None:
            return bool(resp)

    def set(self, value=1):
        self._set(value)

    def clear(self):
        self._set(0)

    def _set(self, v):
        self.handle.ask('Set {} {}'.format(self.name, v))


@provides(IPyScriptRunner)
class RemotePyScriptRunner(PyScriptRunner):
    handle = None

    def __init__(self, host, port, kind, *args, **kw):
        super(RemotePyScriptRunner, self).__init__(*args, **kw)
        self.kind = kind
        self.port = port
        self.host = host
        self.handle = self._handle_factory()

    def reset_connection(self):
        if self.handle.error:
            self.handle = self._handle_factory()
            return self.connect()
        else:
            return True

    def _handle_factory(self):
        handle = EthernetCommunicator()
        handle.host = self.host
        handle.port = self.port
        handle.kind = self.kind
        return handle

    def _get_resource(self, name):
        r = RemoteResource()
        r.name = name
        r.handle = self.handle
        return r

    def connect(self):
        return self.handle.open()


if __name__ == '__main__':
    logging_setup('py_runner')
    p = PyScriptRunner()

    p.configure_traits()
# ============= EOF ====================================
