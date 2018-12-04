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
from datetime import datetime

from traits.api import HasTraits, Str, Bool, Date


# ============= standard library imports ========================
# ============= local library imports  ==========================

class GitTag(HasTraits):
    message = Str
    date = Date
    name = Str
    hexsha = Str
    commit_message = Str

    def __init__(self, obj):
        tag = obj.tag
        commit = obj.commit

        self.name = obj.name
        if tag:
            self.message = tag.message
            self.date = datetime.fromtimestamp(float(tag.tagged_date))

        self.hexsha = commit.hexsha
        self.commit_message = commit.message


class GitSha(HasTraits):
    message = Str
    date = Date
    blob = Str
    name = Str
    hexsha = Str
    author = Str
    email = Str
    active = Bool
    tag = Str

    def _get_summary(self):
        return '{} {}'.format(self.date, self.message)

# ============= EOF =============================================
