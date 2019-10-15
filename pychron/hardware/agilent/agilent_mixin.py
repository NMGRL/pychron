# ===============================================================================
# Copyright 2019 ross
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


class AgilentMixin:
    id_query = '*TST?'

    def id_response(self, response):
        if response.strip() == '0':
            return True

    def initialize(self, *args, **kw):
        ret = super(AgilentMixin, self).initialize(*args, **kw)
        if ret:
            self.communicator.write_terminator = chr(10)
            cmds = self._get_initialization_commands()
            if cmds:
                for c in cmds:
                    self.tell(c)

            self._clear_and_report_errors()
        return ret

    def _get_initialization_commands(self):
        pass

    def _clear_and_report_errors(self):
        self.info('Clear and Report Errors. simulation:{}'.format(self.simulation))

        es = self._get_errors()
        self.info('------------------------ Errors ------------------------')
        if es:
            for ei in es:
                self.warning(ei)
        else:
            self.info('No Errors')
        self.info('--------------------------------------------------------')

    def _get_errors(self):
        # maximum of 10 errors so no reason to use a while loop
        def gen_error():
            for _i in range(10):
                error = self._get_error()
                if error is None:
                    break
                else:
                    yield error

        return list(gen_error())

    def _get_error(self):
        error = None
        cmd = 'SYST:ERR?'
        if not self.simulation:
            s = self.ask(cmd)
            if s is not None:
                s = s.strip()
                if s != '+0,"No error"':
                    error = s

        return error


# ============= EOF =============================================
