# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
import os

from pychron.paths import paths

# ============= standard library imports ========================
# ============= local library imports  ==========================
paths.build('_test')


def launch_device(name, path):
    print 'Launching: {}'.format(name)
    print 'Config File: {}'.format(path)

    from pychron.hardware.pid_controller import DevelopmentPidController

    klass = DevelopmentPidController

    dev = klass(name=name, config_path=path)
    dev.bootstrap()
    dev.setup_scan()
    dev.start_scan()
    print dev
    dev.configure_traits()


if __name__ == '__main__':
    from pychron.core.helpers.logger_setup import logging_setup

    logging_setup('device_launcher')
    name = 'PIDController'
    path = os.path.join(paths.device_dir, 'pid_controller.cfg')
    launch_device(name, path)
# ============= EOF =============================================
