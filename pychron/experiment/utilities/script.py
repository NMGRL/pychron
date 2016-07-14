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

def assemble_script_blob(scripts, kinds=None):
    """
        make one blob of all the script text

        return csv-list of names, blob
    """
    if kinds is None:
        kinds = ['extraction', 'measurement', 'post_equilibration', 'post_measurement']

    ts = []
    for (name, blob), kind in zip(scripts, kinds):
        ts.append('#' + '=' * 79)
        ts.append('# {} SCRIPT {}'.format(kind.replace('_', ' ').upper(), name))
        ts.append('#' + '=' * 79)
        if blob:
            ts.append(blob)

    return 'Pychron Script', '\n'.join(ts)

# ============= EOF =============================================



