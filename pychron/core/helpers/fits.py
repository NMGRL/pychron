#===============================================================================
# Copyright 2012 Jake Ross
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


def convert_fit(f):
    if isinstance(f, (str, unicode)):
        f = f.lower()
        fits = ['linear', 'parabolic', 'cubic']
        if f in fits:
            f = fits.index(f) + 1
        elif 'average' in f:
            if f.endswith('sem'):
                f = 'averageSEM'
            else:
                f = 'averageSD'
        else:
            f = None
    return f


def unconvert_fit(f):
    if isinstance(f, int):
        try:
            f=['linear', 'parabolic','cubic'][f-1]
        except IndexError:
            pass

    return f


#============= EOF =============================================

