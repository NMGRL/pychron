#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
#============= standard library imports ========================
#============= local library imports  ==========================
class GosubError(Exception):
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return 'GosubError: {} does not exist'.format(self.path)

def KlassError(Exceotion):
    def __init__(self, klass):
        self.klass = klass

    def __str__(self):
        return 'KlassError: {} does not exist'.format(self.klass)


class PyscriptError(Exception):
    def __init__(self, name, err):
        self.name = name
        self.err = err

    def __str__(self):
        return 'Pyscript error in {}\n\n{}'.format(self.name, self.err)


class IntervalError(Exception):
    def __str__(self):
        return 'Poorly matched BeginInterval-CompleteInterval'

class MainError(Exception):
    def __str__(self):
        return 'No "main" function defined'

#============= EOF =============================================
