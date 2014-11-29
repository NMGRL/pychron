# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
# ============= standard library imports ========================
# ============= local library imports  ==========================
import os

path = os.environ['PATH']
os.environ['PATH'] = '{}:/usr/local/bin'.format(path)

import objgraph
import random
import inspect

d = dict(a=1, b='2', c=3.0)
objgraph.show_chain(
                    objgraph.find_backref_chain(
                                                random.choice(objgraph.by_type('dict')),
                                                inspect.ismodule),
                    filename='chain.png')


# ============= EOF =============================================
