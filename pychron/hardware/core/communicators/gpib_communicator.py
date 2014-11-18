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
# from traits.api import HasTraits, on_trait_change, Str, Int, Float, Button
# from traitsui.api import View, Item, Group, HGroup, VGroup

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.hardware.core.communicators.communicator import Communicator

# NI_PATH = '/Library/Frameworks/NI488.framework/NI488'


class GpibCommunicator(Communicator):
    pass


#     address = 16
#
#     def load(self, config, path):
#         return True
#
#     def open(self, *args, **kw):
#         try:
#             self.handle = cdll.LoadLibrary(NI_PATH)
#         except:
#             return False
#
#         self.dev_handle = self.handle.ibdev(0, self.address, 0, 4, 1, 0)
#         return True
# #        print self.dev_handle
# #        if self.dev_handle < 0:
# #            self.simulation = True
# #        else:
# #            self.simulation = False
# #
# #
# #        print self.simulation, 'fff'
# #        return not self.simulation
#
#     def ask(self, cmd, verbose=True, *args, **kw):
# #        self.handle.ibask(self.dev_handle)
#         if self.handle is None:
#             if verbose:
#                 self.info('no handle    {}'.format(cmd.strip()))
#             return
#
#         self._lock.acquire()
#         r = ''
#         retries = 5
#         i = 0
#         while len(r) == 0 and i < retries:
#             self._write(cmd)
#             time.sleep(0.05)
#             r = self._read()
#
#             i += 1
#
#         if verbose:
#             self.log_response(cmd, r)
#
#         self.handle.ibclr(self.dev_handle)
#         self._lock.release()
#
#         return r
#
#     def tell(self, *args, **kw):
#         self.write(*args, **kw)
#
#     def write(self, cmd, verbose=True, *args, **kw):
#
#         self._write(cmd, *args, **kw)
#         if verbose:
#             self.info(cmd)
#
#     def _write(self, cmd, *args, **kw):
#         if self.simulation:
#             pass
#         else:
#             cmd += self._terminator
#             self.handle.ibwrt(self.dev_handle, cmd, len(cmd))
#
#     def _read(self):
#         if self.simulation:
#             pass
#         else:
#             b = create_string_buffer('\0' * 4096)
#             retries = 10
#             i = 0
#             while len(b.value) == 0 and i <= retries:
#                 self.handle.ibrd(self.dev_handle, b, 4096)
#                 i += 1
#             return b.value.strip()
#
# if __name__ == '__main__':
#     g = GPIBCommunicator()
#     g.open()
#
#     print g.tell('1HX')
# #    print g.ask('2TP?')

#============= EOF ====================================
