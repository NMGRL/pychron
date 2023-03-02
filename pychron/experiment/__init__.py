# ===============================================================================
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
# ===============================================================================

__version__ = "2.0"


class ExtractionException(BaseException):
    def __init__(self, m):
        self._msg = m


class CheckException(BaseException):
    tag = None

    def __init__(self, msg):
        self._msg = msg

    def __str__(self):
        return "{}: {} Failed".format(self.tag, self._msg)


class PreExtractionCheckException(CheckException):
    tag = "PreExtraction"


class PreExecuteCheckException(CheckException):
    tag = "PreExecute"

    def __init__(self, msg, error=None):
        self._error = error
        super(PreExecuteCheckException, self).__init__(msg)

    def __str__(self):
        r = super(PreExecuteCheckException, self).__str__()
        if r:
            r = "{} {}".format(r, self._error)
        return r


class MessageException(BaseException):
    def __init__(self, msg, error=None):
        self.message = msg
        self._error = error
        super(MessageException, self).__init__(msg)

    def __str__(self):
        r = super(MessageException, self).__str__()
        if r:
            r = "msg={} error={}".format(r, self._error)
        return r
