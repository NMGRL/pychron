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
# ============= standard library imports ========================
# ============= local library imports  ==========================


# class HasCommunicator(ConfigLoadable):
class HasCommunicator(object):
    communicator = None
    id_query = ""
    id_response = ""

    def load_communicator(self, comtype, **kw):
        communicator = self.build_communicator(comtype)
        if communicator is not None:
            communicator.load_comdict(**kw)
            self.communicator = communicator
            return communicator

    def build_communicator(self, comm_type):
        communicator = self._communicator_factory(comm_type)
        if communicator is not None:
            self.communicator = communicator
        return communicator

    def create_communicator(self, comm_type, **kw):
        communicator = self.build_communicator(comm_type)
        if communicator is not None:
            communicator.open(**kw)
            return communicator

    def _communicator_factory(self, communicator_type):
        if communicator_type is not None:
            class_key = "{}Communicator".format(communicator_type.capitalize())
            module_path = "pychron.hardware.core.communicators.{}_communicator".format(
                communicator_type.lower()
            )
            classlist = [class_key]
            try:
                class_factory = __import__(module_path, fromlist=classlist)
                factory = getattr(class_factory, class_key)
            except (ImportError, AttributeError) as e:
                if hasattr(self, "warning"):
                    self.warning(
                        'Failed building communicator "{}" from "{}". {}'.format(
                            class_key, module_path, e
                        )
                    )
                if hasattr(self, "debug_exception"):
                    self.debug_exception()
                return

            return factory(
                name="_".join((self.name, communicator_type.lower())),
                id_query=self.id_query,
                id_response=self.id_response,
            )

    def communicator_available(self):
        return self.communicator is not None

    def close_communicator(self):
        if self.communicator is not None:
            self.communicator.close()

    def require_communicator(self, action=None):
        communicator = self.communicator
        if communicator is None and hasattr(self, "info"):
            msg = "no communicator configured"
            if action:
                msg = "{} for {}".format(msg, action)
            if hasattr(self, "name"):
                msg = "{} {}".format(msg, self.name)
            self.info(msg)
        return communicator

    def open(self, **kw):
        """ """
        communicator = self.require_communicator("open")
        if communicator is not None:
            ret = communicator.open(**kw)
            communicator.report()
            return ret

    # def _communicate_hook(self, cmd, r):
    #     """
    #         hook for subclasses. command and response are passed in
    #     """

    def _load_communicator(self, config, comtype):
        communicator = self.build_communicator(comtype)
        if communicator is not None:
            # give the _communicator the config object so it can load its args
            communicator.load(config, self.config_path)

            if hasattr(self, "id_query"):
                communicator.id_query = getattr(self, "id_query")
            return True

    @property
    def simulation(self):
        sim = True
        if self.communicator:
            sim = self.communicator.simulation
        return sim

    def ask(self, *args, **kw):
        communicator = self.require_communicator("ask")
        if communicator:
            return communicator.ask(*args, **kw)


# ============= EOF =============================================
