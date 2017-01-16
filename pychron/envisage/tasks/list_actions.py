# ===============================================================================
# Copyright 2015 Jake Ross
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
import os
import time
from Queue import Queue, Empty
from threading import Thread

import yaml
from pyface.tasks.action.task_action import TaskAction
from traits.api import Str, Bool
from traitsui.menu import Action

from pychron.core.helpers.filetools import add_extension
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.experiment.automated_run.hop_util import parse_hops, parse_hop
from pychron.lasers.laser_managers.ilaser_manager import ILaserManager
from pychron.paths import paths


class ShowMotionConfigureAction(TaskAction):
    method = 'show_motion_configure'
    name = 'Motion Configure...'


class ListAction(Action):
    pass


class PatternAction(ListAction):
    pattern_path = Str
    manager_name = Str
    lase = Bool(False)

    def perform(self, event):
        app = event.task.application
        man = app.get_service(ILaserManager, 'name=="{}"'.format(self.manager_name))
        man.execute_pattern(self.pattern_path, lase=self.lase)


from traits.api import HasTraits, Int
from traitsui.api import View, Item


class HopConfig(HasTraits):
    ncycles = Int(1)

    def traits_view(self):
        v = View(Item('ncycles', label='Cycles'),
                 buttons=['OK', 'Cancel'],
                 title='Configure Magnet Hops')
        return v


class HopsAction(ListAction):
    hop_name = Str
    _alive = False

    def perform(self, event):

        hc = HopConfig()
        info = hc.edit_traits(kind='livemodal')
        if not info.result:
            return

        p = os.path.join(paths.hops_dir, add_extension(self.hop_name, ext='.yaml'))
        with open(p, 'r') as rfile:
            hops = yaml.load(rfile)

        prog = self._open_prog(hc.ncycles, hops)

        msg_queue = Queue()
        app = event.task.application

        self._alive = True
        producer = Thread(target=self._perform, args=(app, hc.ncycles, hops, msg_queue))
        producer.setDaemon(True)
        producer.start()

        consumer = Thread(target=self._consumer, args=(prog, msg_queue))
        consumer.setDaemon(True)
        consumer.start()

    def _open_prog(self, ncycle, hops):
        from pychron.core.progress import open_progress

        t = 0
        nhops = len(hops)
        for hop in hops:
            hop = parse_hop(hop)
            settle = hop['settle']
            t += settle

        return open_progress(int(t * ncycle + ncycle + nhops))

    def _consumer(self, prog, mq):
        while self._alive:
            if prog.canceled:
                self._alive = False
                break

            try:
                msg = mq.get(timeout=0.1)
                invoke_in_main_thread(prog.change_message, msg)
            except Empty:
                pass
        prog.close()

    def _perform(self, app, ncycles, hops, msg_queue):
        ion = app.get_service('pychron.spectrometer.ion_optics.ion_optics_manager.IonOpticsManager')
        spec = app.get_service('pychron.spectrometer.base_spectrometer_manager.BaseSpectrometerManager')
        for cycle in xrange(ncycles):
            for hop in hops:
                if not self._alive:
                    break

                hop = parse_hop(hop)
                dets = hop['detectors']
                defls = hop['deflections']
                settle = hop['settle']
                pdets = hop['protect_detectors']

                use_dac = False
                positioning = hop['positioning']
                if 'dac' in positioning:
                    use_dac = True
                    isotope = positioning['dac']
                    detector = ''
                else:
                    detector = positioning['detector']
                    isotope = positioning['isotope']

                zd = zip(dets, defls)

                # set deflections
                deflect = len([d for d in defls if d is not None])
                if deflect:
                    for det, defl in zd:
                        spec.set_deflection(det, defl)

                for pd in pdets:
                    spec.protect_detector(pd, True)

                msg_queue.put('Position {} {}'.format(isotope, detector))
                ion.position(isotope, detector, use_dac=use_dac, update_isotopes=False)

                for pd in pdets:
                    spec.protect_detector(pd, False)

                for i in xrange(settle):
                    msg_queue.put('Position {} {}. Settle {}'.format(isotope, detector, settle - i))
                    time.sleep(1)

        self._alive = False


class ProcedureAction(ListAction):
    script_path = Str

    # def __init__(self, *args, **kw):
    #     super(ProcedureAction, self).__init__(*args, **kw)
    #
    #     ex = self.application.get_plugin('pychron.experiment.plugin')
    #     if ex:
    #         ex = ex.experimentor.executor
    #         ex.on_trait_change(self._update_alive, 'alive')

    def _update_alive(self, new):
        self.enabled = not new

    def perform(self, event):
        app = event.task.application

        for tid in ('pychron.experiment.task', 'pychron.spectrometer'):
            task = app.task_is_open(tid)
            if task:
                # make sure extraction line canvas is visible
                task.show_pane('pychron.extraction_line.canvas_dock')
                break
        else:
            # open extraction line task
            task = app.open_task('pychron.extraction_line')
            task.show_pane(task.wait_pane)

        manager = app.get_service('pychron.extraction_line.extraction_line_manager.ExtractionLineManager')

        root = os.path.dirname(self.script_path)
        name = os.path.basename(self.script_path)

        info = lambda x: '======= {} ======='.format(x)

        manager.info(info('Started Procedure "{}"'.format(name)))

        task = app.get_task('pychron.pyscript.task', activate=False)
        context = {'analysis_type': 'blank' if 'blank' in name else 'unknown'}
        task.execute_script(name, root,
                            delay_start=1,
                            manager=manager,
                            on_completion=lambda: manager.info(info('Finished Procedure "{}"'.format(name))),
                            context=context)

# ============= EOF =============================================
