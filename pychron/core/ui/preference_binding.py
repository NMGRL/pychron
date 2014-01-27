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
from apptools.preferences.preference_binding import PreferenceBinding
#============= standard library imports ========================
#============= local library imports  ==========================
# from apptools.preferences.api import PreferenceBinding as TPreferenceBinding
#
class ColorPreferenceBinding(PreferenceBinding):
    def _get_value(self, name, value):
        if 'color' in name:
            value = value.split('(')[1]
            value = value[:-1]
            value = map(float, value.split(','))
            value = ','.join(map(lambda x: str(int(x * 255)), value))
        else:
            value = super(ColorPreferenceBinding, self)._get_value(name, value)
        return value


def color_bind_preference(*args, **kw):
    return bind_preference(factory=ColorPreferenceBinding, *args, **kw)


# Factory function for creating bindings.
def bind_preference(obj, trait_name, preference_path,
                    factory=None,
                    preferences=None):
    # added factory keyword
    # if none use PreferenceBinding

    """ Create a new preference binding. """

    # This may seem a bit wierd, but we manually build up a dictionary of
    # the traits that need to be set at the time the 'PreferenceBinding'
    # instance is created.
    #
    # This is because we only want to set the 'preferences' trait iff one
    # is explicitly specified. If we passed it in with the default argument
    # value of 'None' then it counts as 'setting' the trait which prevents
    # the binding instance from defaulting to the package-global preferences.
    # Also, if we try to set the 'preferences' trait *after* construction time
    # then it is too late as the binding initialization is done in the
    # constructor (we could of course split that out, which may be the 'right'
    # way to do it ;^).
    traits = {
        'obj': obj,
        'trait_name': trait_name,
        'preference_path': preference_path
    }

    if preferences is not None:
        traits['preferences'] = preferences

    if factory is not None:
        return factory(**traits)
    else:
        return PreferenceBinding(**traits)

#============= EOF =============================================
