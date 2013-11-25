#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from pychron.experiment.utilities.human_error_checker import HumanErrorChecker
from pychron.loggable import Loggable
from pychron.experiment.utilities.identifier import get_analysis_type
from pychron.pychron_constants import LINE_STR
#============= standard library imports ========================
#============= local library imports  ==========================

class UVHumanErrorChecker(HumanErrorChecker):
    _extraction_line_required = False
    _mass_spec_required = True

    def _check_run(self, run, inform, test):
        if test:
            run.test_scripts(script_context=self._script_context,
                             warned=self._warned,
                             duration=False)

        err = self._check_attr(run, 'labnumber', inform)
        if err is not None:
            return err

        ant = get_analysis_type(run.labnumber)
        if ant == 'unknown':
            for attr in ('cleanup',):
                err = self._check_attr(run, attr, inform)
                if err is not None:
                    return err

            if run.position:
                if not run.extract_value:
                    return 'position but no extract value'

        #if ant in ('unknown', 'background') or ant.startswith('blank'):
        #self._mass_spec_required = True

        if run.extract_value or run.cleanup:
            self._extraction_line_required = True

    def _check_attr(self, run, attr, inform):
        if not getattr(run, attr):
            msg = 'No {} set for {}'.format(attr, run.runid)
            self.warning(msg)
            if inform:
                self.warning_dialog(msg)
            return 'no {}'.format(attr)

#============= EOF =============================================
