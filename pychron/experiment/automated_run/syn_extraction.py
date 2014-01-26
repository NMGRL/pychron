#===============================================================================
# Copyright 2014 Jake Ross
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
import os
from threading import Thread
import time
from traits.api import HasTraits, Instance, Str, Dict, Property, Bool

#============= standard library imports ========================
#============= local library imports  ==========================
import yaml
from pychron.loggable import Loggable


class SynExtractionSpec(HasTraits):
    mode=Str
    config=Dict

    duration=Property
    end_threshold=Property

    def _get_end_threshold(self):
        if self.config:
            return self.config.get('end_threshold', 10)
        else:
            return 10

    def _get_duration(self):
        if self.config:
            return self.config.get('duration',10)
        else:
            return 10


class SynExtractionCollector(Loggable):
    arun=Instance('pychron.experiment.automated_run.automated_run.AutomatedRun')
    path=Str
    _alive=Bool(False)

    def start(self):
        if not self._get_config():
            self.warning('No configuration available for SynExtraction data collection. '
                         '{} was not found'.format(self.path))
            return

        self._alive=True
        t=Thread(target=self._do_collection)
        t.start()

    def stop(self):
        self._alive=False

    def _do_collection(self):
        gen=self._run_generator()
        starttime=time.time()
        while self._alive:
            et = time.time() - starttime
            run=gen.next()
            if run.mode=='static':
                if run.duration> self.extraction_duration-run.end_threshold-et:
                    self.debug('not enough time to start another static run.'
                               'Run Duration={} Remaining={} '
                               'ExtDuration={} Threshold={} ElapsedTime={}'.format(run.duration,
                                                                                   self.extraction_duration,
                                                                                   run.end_threshold,
                                                                                   et))
                    break
                else:
                    self._do_run(run)
            else:
                if et>self.extraction_duration-run.end_threshold:
                    self.debug('Syn Extraction finished'
                               'Run Duration={} Remaining={} '
                               'ExtDuration={} Threshold={} ElapsedTime={}'.format(run.duration,
                                                                                   self.extraction_duration,
                                                                                   run.end_threshold,
                                                                                   et))
                    break
                else:
                    self._do_run(run)

        self.info('Syn Extraction finished')

    def _do_run(self, run):
        self.debug('Executing SynExtractionSpec mode="{}"'.format(run.mode))

    def _run_generator(self):
        def gen():
            while 1:
                for p in self.pattern:
                    if p=='S':
                        yield self._static_spec_factory()
                    else:
                        yield self._dynamic_spec_factory()

        return gen()

    def _get_config(self):
        p=self.path
        if os.path.isfile(p):
            with open(p, 'r') as fp:
                return yaml.load(fp)

    def _static_spec_factory(self):
        config=self.get_config('static')
        s=SynExtractionSpec(mode='static',
                            config=config)
        return s

    def _dynamic_spec_factory(self):
        config = self.get_config('dynamic')
        s = SynExtractionSpec(mode='dynamic',
                              config=config)
        return s

#============= EOF =============================================

