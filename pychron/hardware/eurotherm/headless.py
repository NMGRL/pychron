# ===============================================================================
# Copyright 2016 Jake Ross
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
from pychron.hardware.core.headless.core_device import HeadlessCoreDevice
from pychron.hardware.eurotherm.base import BaseEurotherm


class HeadlessEurotherm(BaseEurotherm, HeadlessCoreDevice):
    pass


if __name__ == '__main__':
    from pychron.core.helpers.logger_setup import logging_setup
    from pychron.paths import paths
    paths.build('_dev')
    logging_setup('euro', use_archiver=False, use_file=False)
    h = HeadlessEurotherm(name='test_eurotherm', configuration_dir_name='furnace')
    h.bootstrap()

    print h.communicator.handle
    print h.get_process_value()
# ============= EOF =============================================



