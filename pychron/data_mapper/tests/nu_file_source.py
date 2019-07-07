# ===============================================================================
# Copyright 2016 ross
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

# ============= standard library imports ========================
from __future__ import absolute_import
import os
import unittest

from pychron.data_mapper.sources.nu_source import NuFileSource
from pychron.data_mapper.tests import fget_data_dir
from pychron.data_mapper.tests.file_source import BaseFileSourceTestCase


class NuFileSourceUnittest(BaseFileSourceTestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = NuFileSource()
        p = os.path.join(fget_data_dir(), 'Data_NAG1072.RUN')
        pnice = os.path.join(fget_data_dir(), 'wiscar.nice')
        cls.src.path = p
        cls.src.nice_path = pnice
        cls.spec = cls.src.get_analysis_import_spec()

        cls.expected = {'runid': 'Data_NAG1072',
                        # 'irradiation': 'IRR347',
                        # 'irradiation_level': 'A',
                        # 'sample': 'GA1550',
                        # 'material': 'Bio',
                        # 'project': 'Std',
                        # 'j': 0.0045,
                        # 'j_err': 1e-7,
                        'timestamp_month': 6,
                        'cnt40': 200,
                        'cnt39': 200,
                        'cnt38': 200,
                        'cnt37': 200,
                        'cnt36': 200,
                        'discrimination': 1.0462399093612802,
                        'uuid': 'Data_NAG1072'
                        }



if __name__ == '__main__':
    unittest.main()

# ============= EOF =============================================
