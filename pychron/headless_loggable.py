# ===============================================================================
# Copyright 2016 Jake Ross
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
from traits.api import HasTraits, Str, Int, Bool, Any, Float, Property, on_trait_change

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.logger_setup import new_logger


class HeadlessLoggable(HasTraits):
    def __init__(self, *args, **kw):
        super(HeadlessLoggable, self).__init__(*args, **kw)

        if self.logger_name:
            name = self.logger_name
        elif self.name:
            name = self.name
        else:
            name = self.__class__.__name__

        self.logger = new_logger(name)

    def info(self, msg, **kw):
        self.logger.info(msg)

    def warning(self, msg, **kw):
        self.logger.warning(msg)

    def debug(self, msg, **kw):
        self.logger.debug(msg)

    def critical(self, msg, **kw):
        self.logger.critcial(msg)

# ============= EOF =============================================
