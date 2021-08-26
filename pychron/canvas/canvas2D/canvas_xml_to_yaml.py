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

import yaml


class CanvasConverter:
    def __init__(self, path):
        self.path = path

    def toyaml(self):
        obj = {''}

        output, tail = os.path.splitext(os.path.basename(self.path))
        root = os.path.dirname(self.path)
        p = os.path.join(root, '{}.yaml'.format(output))
        with open(p, 'w') as wfile:
            yaml.dump(obj, wfile)

# ============= EOF =============================================
