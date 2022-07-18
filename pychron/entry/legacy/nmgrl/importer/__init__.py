# ===============================================================================
# Copyright 2020 ross
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
from pychron.entry.legacy.util import get_dvc


class BaseImporter:
    _dvc = None

    def __init__(self, dvc=None):
        self._cache = []
        self._dvc = dvc
        self._load()

    def do_import(self, run):
        raise NotImplementedError

    def _load(self):
        pass


# ============= EOF =============================================
