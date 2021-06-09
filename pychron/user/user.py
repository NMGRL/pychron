# ===============================================================================
# Copyright 2021 ross
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


# ============= EOF =============================================
from traits.has_traits import HasTraits
from traits.trait_types import Str, Bool


class User(HasTraits):
    name = Str
    email = Str
    enabled = Bool
    keys = ('name', 'email', 'enabled')

    def __init__(self, dbrecord, *args, **kw):
        super(User, self).__init__(*args, **kw)
        self.name = dbrecord.name
        self.email = dbrecord.email or ''