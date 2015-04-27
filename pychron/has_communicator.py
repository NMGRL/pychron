# ===============================================================================
# Copyright 2012 Jake Ross
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
# from traits.api import HasTraits
# from traitsui.api import View, Item, TableEditor
# ============= standard library imports ========================
# ============= local library imports  ==========================


# class HasCommunicator(ConfigLoadable):
class HasCommunicator(object):
    _communicator = None
    id_query = ''
    id_response = ''

    def create_communicator(self, comm_type, port, baudrate):

        c = self._communicator_factory(comm_type)
        c.open(port=port, baudrate=baudrate)
        self._communicator = c

    def _communicator_factory(self, communicator_type):
        if communicator_type is not None:
            class_key = '{}Communicator'.format(communicator_type.capitalize())
            module_path = 'pychron.hardware.core.communicators.{}_communicator'.format(communicator_type.lower())
            classlist = [class_key]

            class_factory = __import__(module_path, fromlist=classlist)
            return getattr(class_factory, class_key)(name='_'.join((self.name, communicator_type.lower())),
                                                     id_query=self.id_query,
                                                     id_response=self.id_response)

    def open(self, **kw):
        """
        """
        if self._communicator is not None:
            return self._communicator.open(**kw)

    def _communicate_hook(self, cmd, r):
        """
            hook for subclasses. command and response are passed in
        """

    def _load_communicator(self, config, comtype):
        communicator = self._communicator_factory(comtype)
        if communicator is not None:
            # give the _communicator the config object so it can load its args
            communicator.load(config, self.config_path)

            if hasattr(self, 'id_query'):
                communicator.id_query = getattr(self, 'id_query')
            self._communicator = communicator
            return True

# ============= EOF =============================================
