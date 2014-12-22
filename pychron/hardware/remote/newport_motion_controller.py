# ===============================================================================
# Copyright 2013 Jake Ross
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

# ============= enthought library imports =======================
from pychron.hardware.newport.newport_motion_controller import NewportMotionController
from pychron.rpc.query import rpc_query
# ============= standard library imports ========================
# ============= local library imports  ==========================

class RemoteNewportMotionController(NewportMotionController):
    @rpc_query
    def ask(self, *args, **kw):
        pass
    @rpc_query
    def tell(self, *args, **kw):
        pass

#     @rpc_query
#     def get_current_position(self, *args, **kw):
#         pass
#     @rpc_query
#     def relative_move(self, *args, **kw):
#         pass
#     @rpc_query
#     def multiple_point(self, *args, **kw):
#         pass
#     @rpc_query
#     def linear_move(self, *args, **kw):
#         pass
#     @rpc_query
#     def linear_move(self, *args, **kw):
#         pass
#     @rpc_query
#     def linear_move(self, *args, **kw):
#         pass


# ============= EOF =============================================
