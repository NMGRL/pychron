# ===============================================================================
# Copyright 2015 Jake Ross
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


def import_klass(k):
    """
        e.g. importstr= a.b.c.klass
        similar to
        from a.b.c import klass

    :param importstr:
    :return: classobj
    """
    args = k.split('.')
    pkg, klass = '.'.join(args[:-1]), args[-1]
    mod = __import__(pkg, fromlist=[klass])

    return getattr(mod, klass)

# ============= EOF =============================================
