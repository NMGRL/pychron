# ===============================================================================
# Copyright 2018 ross
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
from datetime import datetime


class DVCCache(object):
    def __init__(self, max_size=1000):
        self._cache = {}
        self.max_size = max_size

    def clear(self):
        self._cache.clear()

    def clean(self):
        t = 60 * 15  # 15 minutes
        now = datetime.now()
        remove = (k for k, v in self._cache.items()
                  if (now - v['date_accessed']).total_seconds() > t)

        for k in remove:
            del self._cache[k]

    def report(self):
        return len(self._cache)

    def get(self, item):
        obj = self._cache.get(item)
        if obj:
            obj['date_accessed'] = datetime.now()
            return obj['value']

    def update(self, key, value):
        if key not in self._cache and len(self._cache) > self.max_size:
            self.remove_oldest()

        self._cache[key] = {'date_accessed': datetime.now(),
                            'value': value}

    def remove_oldest(self):
        """
                Remove the entry that has the oldest accessed date
        """
        oldest_entry = None
        for key in self._cache:
            if oldest_entry is None:
                oldest_entry = key
            elif self._cache[key]['date_accessed'] < self._cache[oldest_entry]['date_accessed']:
                oldest_entry = key

        self._cache.pop(oldest_entry)
# ============= EOF =============================================
