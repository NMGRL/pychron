# ===============================================================================
# Copyright 2023 Jake Ross
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
import time

from pychron.hardware.core.core_device import CoreDevice


class LasconController(CoreDevice):
    def initialize(self, *args, **kw):
        self.communicator.write_terminator = "\r\n"
        self.communicator.read_terminator = "\r\n"
        self.debug(f"initialize response ={self.read()}")

        # login as master
        self.ask("SendPassword 3")
        return True

    def set(self, script_number, block=True):
        self.ask(f"PScriptLoad {script_number}")
        self.ask(f"PScriptSet {script_number}")

    def send_script(self, text, script_number, stop_on_completion):
        sleep = 0
        self.ask(f"PScriptStart {script_number}")
        for t in text.split("\n"):
            t = t.strip()
            if t:
                self.ask(f"PScriptAdd {t}")

                # calculate how long to wait
                t = t.lower()
                if t.startswith("wait"):
                    _, p, *_ = t.split(" ")
                    sleep += float(p) / 1000

        end = "STOP" if stop_on_completion else "END"
        self.ask(f"PScriptAdd {end}")

        self.ask("PScriptEnd")
        return sleep

    def load_and_execute_script(self, text, stop_on_completion=True):
        # self.ask('GetRights')
        # self.ask('GetCoreStatus')

        # self.ask('GetStatus')

        script_number = 2
        sleep = self.send_script(text, script_number, stop_on_completion)

        # load
        self.ask(f"PScriptLoad {script_number}")
        self.ask(f"PScriptSet 1 {script_number}")

        # set this script to trigger via TCP
        self.ask(f"PScriptSelect 1 {script_number}")

        # start the process and process script.
        self.ask("ProcStart")

        # procstart triggers a few other messages
        # while 1:
        #     time.sleep(0.5)
        #     resp = self.communicator.readline()
        #     if resp is None:
        #         break
        #     resp = resp.lower().strip()
        #     if resp.startswith('procstart'):
        #         self.debug('Process successfully started')
        #         break

        # pad sleep
        sleep *= 1.25

        st = time.time()
        while 1:
            resp = self.ask("GetCoreStatus")
            if resp is not None:
                resp = resp.strip().lower()
                if resp == "getcorestatus 3 0 0 0":
                    self.debug("Process stopped")
                    break

            if time.time() - st > sleep:
                self.debug("timeout")
                self.ask("ProcStop")
                break

            time.sleep(1)

    def set_settings(self, name):
        # self.ask('GetCoreStatus')
        # self.ask('SetCoreStatus 3')
        # self.ask('GetSetting')
        self.ask(f"SetSetting {name}")
        # self.ask('GetSetting')
        # self.ask('PScriptList')

    # def read_scripts(self):
    #     self.ask('PScriptList')
    #     self.ask('PScriptExists 2')

    # def load_and_execute_script(self, script_number, block=True):
    #     self.ask(f'PScriptLoad {script_number}')
    #     self.ask(f'PScriptSet {script_number}')

    #     if block:
    #         if isinstance(block, bool):
    #             block = 5

    #         while 1:
    #             resp = self.ask('PScriptGet')
    #             if resp == '0':
    #                 break
    #             time.sleep(block)


# ============= EOF =============================================
