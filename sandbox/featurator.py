# ===============================================================================
# Copyright 2011 Jake Ross
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



from pychron.remote_hardware.protocols.laser_protocol import LaserProtocol

'''
test features of pychron using unittest



'''
#=============enthought library imports=======================
#============= standard library imports ========================
#============= local library imports  ==========================
import subprocess
import time

# ===============================================================================
# ImportTest
# ===============================================================================
# class ImportTest(unittest.TestCase):
#
#    def setUp(self):
#        pass
#    def testELM(self):
#        from pychron.managers.extraction_line_manager import ExtractionLineManager
#        e = ExtractionLineManager()
#        self.assertEqual(e.__class__, ExtractionLineManager)
#
#    def testFusionsCO2(self):
#        from pychron.managers.laser_managers.fusions_co2_manager import FusionsCO2Manager
#        e = FusionsCO2Manager()
#        self.assertEqual(e.__class__, FusionsCO2Manager)
#
#    def testFusionsDiode(self):
#        from pychron.managers.laser_managers.fusions_diode_manager import FusionsDiodeManager
#        e = FusionsDiodeManager()
#        self.assertEqual(e.__class__, FusionsDiodeManager)
#
#    def testStageManager(self):
#        from pychron.managers.stage_managers.stage_manager import StageManager
#        e = StageManager()
#        self.assertEqual(e.__class__, StageManager)
#
#    def testVideoStageManager(self):
#        from pychron.managers.stage_managers.video_stage_manager import VideoStageManager
#        e = VideoStageManager()
#        self.assertEqual(e.__class__, VideoStageManager)

# ===============================================================================
# RemoteHardwareTest
# ===============================================================================

# from pychron.remote_hardware.tests.laser_test import LaserTest
# from pychron.remote_hardware.tests.system_test import SystemTest


def test(protocol, client):
    print '=' * 80
    print 'Testing commands'
    print '=' * 80
    print
    for k, v in protocol.commands.iteritems():
        delay = 0.25
        if isinstance(v, tuple):
            delay = v[1]
            v = v[0]
        cmd = '{} {}'.format(k, v) if v is not None else k
        _resp = client.ask(cmd)
        time.sleep(delay)

    print
    print '=' * 80
    print 'Finished testing commands'
    print '=' * 80


def main(launch=False, simulator=False):
    if launch:
        # launch pychron
        subprocess.Popen(['python', './launchers/pychron_beta.py'])
        # launch remote hardware server
        subprocess.Popen(['python', './launchers/remote_hardware_server.py'])
        # use testclient to send commands
    #        time.sleep()
    else:
    #    run_test = raw_input(' execute test y/n [y]>> ') == '' or 'y'
    #    if not run_test:
    #        return
        from pychron.messaging.testclient import Client

        client = Client(host='localhost',
                        port=1063)
        if simulator:
            mass_spec_simulator(client)
        else:
            from pychron.remote_hardware.protocols.system_protocol import SystemProtocol

            test(SystemProtocol(), client)

            client.port = 1068
            test(LaserProtocol(), client)


def mass_spec_simulator(client):
    client.ask('StartMultRuns Foo')
    client.ask('StartRun DDD')

    client.ask('SetXY 10,10', port=1067)
    client.ask('Enable', port=1067)
    time.sleep(3)
    client.ask('Disable', port=1067)
    time.sleep(3)
    client.ask('CompleteRun DDD')

#    _lock = Lock()
#
#    def _sim():
#        for i in range(100):
#            with _lock:
#                client.ask('GetValveStates', port=1063)
#            time.sleep(1)
#
#    t = Thread(target=_sim)
#    t.start()
#
#    time.sleep(1)
#
#    for cmd, d in [('Enable', 5), ('Disable', 0.1)]:
#        with _lock:
#            client.ask(cmd, port=1067)
#        time.sleep(d)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--launch', action='store_true')
    parser.add_argument('-s', '--simulator', action='store_true')

    args = parser.parse_args()
    main(launch=args.launch,
         simulator=args.simulator)

#============= EOF =====================================

