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
from traits.api import HasTraits, Instance, Str, Dict, Property, Bool, Float

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
            return self.config.get('end_threshold', 0)
        else:
            return 0

    def _get_duration(self):
        if self.config:
            return self.config.get('duration',5)
        else:
            return 5


class SynExtractionCollector(Loggable):
    arun=Instance('pychron.experiment.automated_run.automated_run.AutomatedRun')
    path=Str
    _alive=Bool(False)

    extraction_duration=Float

    def start(self):
        yd=self._load_config()
        if yd:

            self._alive = True
            t = Thread(target=self._do_collection, args=(yd, ))
            t.start()
        else:
            self.warning('No configuration available for SynExtraction data collection. '
                         '{} was not found'.format(self.path))

    def stop(self):
        self._alive=False

    def _do_collection(self, cfg):
        self.info('Starting syn extraction collection')

        gen=self._run_generator(cfg)
        starttime=time.time()
        while self._alive:
            et = time.time() - starttime
            run=gen.next()
            if not run:
                self.warning('Failed getting a syn extraction spec')
                break

            if run.mode=='static':
                rem=self.extraction_duration-run.end_threshold-et
                if run.duration> rem:
                    self.debug('not enough time to start another static run.'
                               'Run Duration={} Remaining={} '
                               'ExtDuration={} Threshold={} ElapsedTime={}'.format(run.duration,
                                                                                   rem,
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
        time.sleep(run.duration)

    def _run_generator(self, config):
        pattern=config.get('pattern','S')
        def gen():
            while 1:
                for p in pattern:
                    if p=='S':
                        yield self._static_spec_factory(config)
                    else:
                        yield self._dynamic_spec_factory(config)

        return gen()

    def _load_config(self):
        p=self.path
        if os.path.isfile(p):
            with open(p, 'r') as fp:
                return yaml.load(fp)

    def _static_spec_factory(self, config):
        config=config.get('static')
        if config:
            s=SynExtractionSpec(mode='static',
                                config=config)
            return s
        else:
            self.debug('no static in configuration file')

    def _dynamic_spec_factory(self, config):
        config = config.get('dynamic')
        if config:
            s = SynExtractionSpec(mode='dynamic',
                                  config=config)
            return s
        else:
            self.debug('no dynamic in configuration file')

#============= EOF =============================================

