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
from traits.api import Bool

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.ui.preference_binding import bind_preference
from pychron.experiment.utilities.identifier import get_analysis_type
from pychron.loggable import Loggable
from pychron.pychron_constants import LINE_STR, SCRIPT_NAMES, NULL_STR


class HumanErrorChecker(Loggable):
    _extraction_line_required = False
    _mass_spec_required = True
    extraction_script_enabled = Bool(True)
    queue_enabled = Bool(True)
    runs_enabled = Bool(True)
    non_fatal_enabled = Bool(True)

    def __init__(self, *args, **kw):
        super(HumanErrorChecker, self).__init__(*args, **kw)

        self._bind_preferences()

    def check_queue(self, qi):
        if self.queue_enabled:
            self.info('check queue disabled')
            return

        self.info('check queue {}'.format(qi.name))
        if self._extraction_line_required:
            if not qi.extract_device or qi.extract_device in ('Extract Device',):
                if not self.confirmation_dialog('No extract device set.\n'
                                                'Are you sure you want to continue?'):
                    msg = '"Extract Device is not set". Not saving experiment!'
                    self.info(msg)
                    return msg

        if self._mass_spec_required:
            if not qi.mass_spectrometer or \
                            qi.mass_spectrometer in ('Spectrometer',):
                msg = '"Spectrometer" is not set. Not saving experiment!'
                return msg

    def check_runs_non_fatal(self, runs):
        if not self.non_fatal_enabled:
            self.info('check runs non fatal disabled')
            return

        for i, r in enumerate(runs):
            ret = self._check_run_non_fatal(i, r)
            if ret:
                return ret

    _script_context = None
    _warned = None

    def check_runs(self, runs, test_all=False, inform=True,
                   test_scripts=False):

        if not self.runs_enabled:
            self.info('check runs disabled')
            return

        ret = dict()

        self._script_context = {}
        self._warned = []
        inform = inform and not test_all
        for i, ai in enumerate(runs):
            err = self._check_run(ai, inform, test_scripts)
            if err is not None:
                ai.state = 'invalid'
                ret['{}. {}'.format(i + 1, ai.runid)] = err
                if not test_all:
                    return ret
            else:
                ai.state = 'not run'

        del self._script_context
        del self._warned

        return ret

    def report_errors(self, errdict):

        msg = '\n'.join(['{} {}'.format(k, v) for k, v in errdict.iteritems()])
        self.warning_dialog(msg)

    def check_run(self, run, inform=True, test=False):
        return self._check_run(run, inform, test)

    def _check_run_non_fatal(self, idx, run):
        es = run.extraction_script
        if es:
            es = es.lower()

        # check for all scripts
        for s in SCRIPT_NAMES:
            ss = getattr(run, s)
            if not ss or ss == NULL_STR:
                return 'Missing "{}" for run={} {} pos={}'.format(s.upper(), idx + 1, run.runid, run.position)

        ed = run.extract_device
        if self.extraction_script_enabled:
            if run.analysis_type == 'unknown' and ed not in ('Extract Device', LINE_STR, 'No Extract Device') and es:
                ds = ed.split(' ')[1].lower()
                if ds not in es:
                    return 'Extraction script "{}" does not match the default "{}". An easy solution is to make sure ' \
                           '"{}" is in the name of the extraction script'.format(es, ds, ds)
            elif run.analysis_type == 'cocktail' and es and 'cocktail' not in es:
                return 'Cocktail analysis is not using a "cocktail" extraction script'
            elif run.analysis_type == 'air' and es and 'air' not in es:
                return 'Air analysis is not using an "air" extraction script'

    # private
    def _bind_preferences(self):
        bind_preference(self, 'extraction_script_enabled', 'pychron.experiment.extraction_script_enabled')
        bind_preference(self, 'runs_enabled', 'pychron.experiment.runs_enabled')
        bind_preference(self, 'queue_enabled', 'pychron.experiment.queue_enabled')
        bind_preference(self, 'non_fatal_enabled', 'pychron.experiment.non_fatal_enabled')

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

            for attr in ('duration', 'cleanup'):
                err = self._check_attr(run, attr, inform)
                if err is not None:
                    return err

            if run.position:
                if not run.extract_value:
                    return 'position but no extract value'

            if run.overlap[0]:
                if not run.post_measurement_script:
                    return 'post measurement script required for overlap'
        # if ant in ('unknown', 'background') or ant.startswith('blank'):
        # self._mass_spec_required = True

        if run.extract_value or run.cleanup or run.duration:
            self._extraction_line_required = True

    def _check_attr(self, run, attr, inform):
        if not getattr(run, attr):
            msg = 'No {} set for {}'.format(attr, run.runid)
            self.warning(msg)
            if inform:
                self.warning_dialog(msg)
            return 'no {}'.format(attr)

# ============= EOF =============================================
