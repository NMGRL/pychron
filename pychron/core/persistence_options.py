# ===============================================================================
# Copyright 2016 ross
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
import os

from traits.api import HasTraits

from pychron.paths import paths
from pychron.persistence_loggable import PersistenceMixin

try:

    class BasePersistenceOptions(HasTraits, PersistenceMixin):
        def __init__(self, *args, **kw):
            self.set_persistence_path()
            self.load()

        def set_persistence_path(self, name=None):
            if not name:
                name = self._persistence_name

            self.persistence_path = os.path.join(paths.appdata_dir, name)

except TypeError:
    # documentation auto doc hack
    class BasePersistenceOptions:
        pass


# ============= EOF =============================================
