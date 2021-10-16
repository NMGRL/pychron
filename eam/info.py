# ===============================================================================
# Copyright 2021 ross
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
import os

HERE = os.path.abspath(os.path.dirname(__file__))


def info():
    """ Provides information to the "eam" package.
  """
    icon = os.path.join(HERE, '../resources', 'apps', 'pyview_icon.icns')
    return {
        'name': 'Pycrunch',
        'description': 'Pychron data reduction',
        'license': 'BSD',
        'copyright': '(c) 2021 PychronLabs',
        'version': u'0.0.1',
        'schema_version': 2,
        'commands': [
            {'name': 'hello',
             'command': 'pycrunch',
             'shortcut': 'desktop',
             'icon': icon,
             'schema_version': 2}]}

# ============= EOF =============================================
