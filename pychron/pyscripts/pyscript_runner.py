#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import Any, Dict, List
from traitsui.api import View, Item, TableEditor
#============= standard library imports ========================
from threading import Event, Lock
#============= local library imports  ==========================
from pychron.core.helpers.logger_setup import logging_setup
from traitsui.table_column import ObjectColumn
from traitsui.extras.checkbox_column import CheckboxColumn
from pychron.viewable import Viewable
from pychron.hardware.core.communicators.ethernet_communicator import EthernetCommunicator


class PyScriptRunner(Viewable):
    resources = Dict
    _resource_lock = Any
    scripts = List

#    @on_trait_change('scripts[]')
#    def _scripts_changed(self, obj, name, old, new):
#        if not len(self.scripts):
#            self.close_ui()
    def connect(self):
        return True

    def __resource_lock_default(self):
        return Lock()

    def get_resource(self, resource):
        with self._resource_lock:
            if not resource in self.resources:
                self.resources[resource] = self._get_resource(resource)

            r = self.resources[resource]
            return r

    def _get_resource(self, name):
        return Event()

    def traits_view(self):

        cols = [ObjectColumn(name='logger_name', label='Name',
                              editable=False, width=150),
                CheckboxColumn(name='cancel_flag', label='Cancel',
                               width=50),
              ]
        v = View(Item('scripts', editor=TableEditor(columns=cols,
                                                    auto_size=False),
                      show_label=False
                      ),
                 width=500,
                 height=500,
                 resizable=True,
                 handler=self.handler_klass(),
                 title='ScriptRunner'
                 )
        return v



class RemoteResource(object):
    handle = None
    name = None

#===============================================================================
# threading.Event interface
#===============================================================================
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

class RemotePyScriptRunner(PyScriptRunner):
    handle = None
    def __init__(self, host, port, kind, *args, **kw):
        super(RemotePyScriptRunner, self).__init__(*args, **kw)
        self.handle = EthernetCommunicator()
        self.handle.host = host
        self.handle.port = port
        self.handle.kind = kind
#        self.handle.open()

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
#============= EOF ====================================
