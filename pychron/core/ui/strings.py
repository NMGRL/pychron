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

# ============= enthought library imports =======================
# ============= standard library imports ========================
# ============= local library imports  ==========================
from __future__ import absolute_import
import re

from traits.trait_types import BaseStr
import six

pascalcase_regex = re.compile(r"^[A-Z](([a-z0-9]+[A-Z]?)*)$")
reponame_regex = re.compile(r"^[\w_-]+$")
experiment_name_regex = re.compile(r"^([0-9]+)?([A-Za-z0-9]+)$")


class PascalCase(BaseStr):
    def validate(self, obj, name, value):
        if not value or not pascalcase_regex.match(value):
            self.error(obj, name, value)
        else:
            return value


class SpacelessStr(BaseStr):
    def validate(self, obj, name, value):
        if isinstance(value, six.string_types) and " " not in value:
            return value

        self.error(obj, name, value)


class RepoNameStr(BaseStr):
    def validate(self, obj, name, value):
        if not value or not reponame_regex.match(value):
            self.error(obj, name, value)
        else:
            return value


class ExperimentStr(BaseStr):
    def validate(self, obj, name, value):
        if not value or not experiment_name_regex.match(value):
            self.error(obj, name, value)
        else:
            return value


# ============= EOF =============================================
