# ===============================================================================
# Copyright 2014 Jake Ross
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
from traits.api import BaseStr, Int
# ============= standard library imports ========================
import re
# ============= local library imports  ==========================
from pychron.core.filtering import validate_filter_predicate

IPREGEX = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')


class IPAddress(BaseStr):
    def validate(self, obj, name, value):
        if not value or value == 'localhost' or IPREGEX.match(value):
            return value
        else:
            self.error(obj, name, value)


class PositiveInteger(Int):
    def validate(self, object, name, value):
        if value >= 0:
            return value

        self.error(object, name, value)


class FilterPredicate(BaseStr):
    def validate(self, obj, name, value):
        if not value or self._validate(value):
            return value
        else:
            self.error(obj, name, value)

    def _validate(self, value):
        return validate_filter_predicate(value)

# ============= EOF =============================================
