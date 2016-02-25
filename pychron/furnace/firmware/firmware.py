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

# from pychron.core.helpers.logger_setup import logging_setup
# from pychron.paths import paths
# from pychron.headless_loggable import HeadlessLoggable
#
#
# class Firmware(HeadlessLoggable):
#     manager = None
#     server = None
#
#     def bootstrap(self, **kw):
#         self.info('---------------------------------------------')
#         self.info('----------- Bootstrapping Firmware -----------')
#         self.info('---------------------------------------------')
#
#         from pychron.furnace.firmware.manager import FirmwareManager
#         from pychron.furnace.firmware.server import FirmwareServer
#         self.manager = FirmwareManager()
#         self.manager.bootstrap(**kw)
#         self.server = FirmwareServer(manager=self.manager)
#         self.server.bootstrap(**kw)


def run():
    print 'run'
    # import argparse

    # paths.build('_dev')

    # logging_setup('furnace_firmware', use_archiver=False)
    # parser = argparse.ArgumentParser(description='Run NMGRL Furnace Firmware')

    # parser.add_argument('--host',
    #                     type=str,
    #                     default='127.0.0.1',
    #                     help='host')

    # parser.add_argument('--port',
    #                     type=int,
    #                     default=4567,
    #                     help='TCP port to listen')

    # parser.add_argument('--debug',
    #                     action='store_true',
    #                     default=False,
    #                     help='run in debug mode')

    # fm = Firmware()
    # fm.bootstrap(**vars(parser.parse_args()))

if __name__ == '__main__':
    run()

# ============= EOF =============================================
