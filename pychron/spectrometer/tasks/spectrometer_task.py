# ===============================================================================
# Copyright 2013 Jake Ross
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
from __future__ import absolute_import

import time

# ============= standard library imports ========================
from threading import Thread

from pyface.tasks.action.schema import SToolBar
from pyface.tasks.task_layout import TaskLayout, PaneItem, Splitter, VSplitter
from pyface.ui.qt.tasks.advanced_editor_area_pane import EditorWidget
from traits.api import Any, Instance, on_trait_change

# ============= local library imports  ==========================
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.envisage.tasks.editor_task import EditorTask
from pychron.spectrometer.tasks.editor import (
    PeakCenterEditor,
    ScanEditor,
    CoincidenceEditor,
    ScannerEditor,
)
from pychron.spectrometer.tasks.spectrometer_actions import StopScanAction
from pychron.spectrometer.tasks.spectrometer_panes import (
    ControlsPane,
    ReadoutPane,
    IntensitiesPane,
    RecordControlsPane,
    DACScannerPane,
    MassScannerPane,
)


class SpectrometerTask(EditorTask):
    scan_manager = Any
    name = "Spectrometer"
    id = "pychron.spectrometer"
    _scan_editor = Instance(ScanEditor)
    tool_bars = [
        SToolBar(
            StopScanAction(),
        )
    ]

    def info(self, msg, *args, **kw):
        super(SpectrometerTask, self).info(msg)

    def spy_position_magnet(self, *args, **kw):
        self.scan_manager.position_magnet(*args, **kw)

    def spy_peak_center(self, name):
        peak_kw = dict(
            confirm_save=False,
            warn=True,
            new_thread=False,
            message="spectrometer script peakcenter",
            on_end=self._on_peak_center_end,
        )
        setup_kw = dict(config_name=name)

        return self._peak_center(setup_kw=setup_kw, peak_kw=peak_kw)

    def populate_mftable(self):
        sm = self.scan_manager
        cfg = sm.setup_populate_mftable()
        if cfg:

            def func():
                refiso = cfg.isotope
                ion = sm.ion_optics_manager
                ion.backup_mftable()

                odefl = []
                dets = cfg.get_detectors()
                self.debug("setting deflections")
                for det, defl in dets:
                    odefl.append((det, sm.spectrometer.get_deflection(det)))
                    sm.spectrometer.set_deflection(det, defl)

                for di in dets:
                    ion.setup_peak_center(
                        detector=[di.name],
                        isotope=refiso,
                        config_name=cfg.peak_center_config.active_item.name,
                        standalone_graph=False,
                        new=True,
                        show_label=True,
                        use_configuration_dac=False,
                    )

                    ion.peak_center.update_others = False
                    name = "Pop MFTable {}-{}".format(di.name, refiso)
                    invoke_in_main_thread(
                        self._open_editor,
                        PeakCenterEditor(model=ion.peak_center, name=name),
                    )

                    self._on_peak_center_start()
                    ion.do_peak_center(new_thread=False, save=True, warn=True)
                    self._on_peak_center_end()
                    if not ion.peak_center.isAlive():
                        break

                self.debug("unset deflections")
                for det, defl in odefl:
                    sm.spectrometer.set_deflection(det, defl)

                fp = cfg.get_finish_position()
                self.debug("move to end position={}".format(fp))
                if fp:
                    iso, det = fp
                    if iso and det:
                        ion.position(iso, det)

            t = Thread(target=func)
            t.start()

    def stop_scan(self):
        self.debug("stop scan fired")
        editor = self.active_editor
        self.debug("active editor {}".format(editor))
        if editor:
            if isinstance(editor, (ScanEditor, PeakCenterEditor, CoincidenceEditor)):
                self.debug("editor stop")
                editor.stop()

    def do_coincidence(self):
        es = [
            int(e.name.split(" ")[-1])
            for e in self.editor_area.editors
            if isinstance(e, CoincidenceEditor)
        ]

        i = max(es) + 1 if es else 1
        man = self.scan_manager.ion_optics_manager
        name = "Coincidence {:02d}".format(i)

        if man.setup_coincidence():
            self._open_editor(CoincidenceEditor(model=man.coincidence, name=name))
            man.do_coincidence_scan()

    def do_peak_center(self):
        peak_kw = dict(
            confirm_save=True,
            warn=True,
            message="manual peakcenter",
            on_end=self._on_peak_center_end,
        )
        self._peak_center(peak_kw=peak_kw)

    def define_peak_center(self):
        from pychron.spectrometer.ion_optics.define_peak_center_view import (
            DefinePeakCenterView,
        )

        man = self.scan_manager.ion_optics_manager
        spec = man.spectrometer
        dets = spec.detector_names
        isos = spec.isotopes

        dpc = DefinePeakCenterView(
            detectors=dets, isotopes=isos, detector=dets[0], isotope=isos[0]
        )
        info = dpc.edit_traits()
        if info.result:
            det = dpc.detector
            isotope = dpc.isotope
            dac = dpc.dac
            self.debug("manually setting mftable to {}:{}:{}".format(det, isotope, dac))
            message = "manually define peak center {}:{}:{}".format(det, isotope, dac)
            man.spectrometer.magnet.update_field_table(det, isotope, dac, message)

    def _on_peak_center_start(self):
        self.scan_manager.log_events_enabled = False
        self.scan_manager.scan_enabled = False

    def _on_peak_center_end(self):
        self.scan_manager.log_events_enabled = True
        self.scan_manager.scan_enabled = True

    def send_configuration(self):
        self.scan_manager.spectrometer.send_configuration()

    def prepare_destroy(self):
        for e in self.editor_area.editors:
            if hasattr(e, "stop"):
                e.stop()

        self.scan_manager.prepare_destroy()
        super(SpectrometerTask, self).prepare_destroy()

    # def activated(self):
    # self.scan_manager.activate()
    # self._scan_factory()
    # super(SpectrometerTask, self).activated()

    def create_dock_panes(self):
        panes = [
            ControlsPane(model=self.scan_manager),
            RecordControlsPane(model=self.scan_manager),
            MassScannerPane(model=self.scan_manager),
            DACScannerPane(model=self.scan_manager),
            ReadoutPane(model=self.scan_manager),
            IntensitiesPane(model=self.scan_manager),
        ]

        panes = self._add_canvas_pane(panes)
        return panes

    # def _active_editor_changed(self, new):
    # if not new:
    #         try:
    #             self._scan_factory()
    #         except AttributeError:
    #             pass

    # private
    def _peak_center(self, setup_kw=None, peak_kw=None):
        if setup_kw is None:
            setup_kw = {}

        if peak_kw is None:
            peak_kw = {}

        es = []
        for e in self.editor_area.editors:
            if isinstance(e, PeakCenterEditor):
                try:
                    es.append(int(e.name.split(" ")[-1]))
                except ValueError:
                    pass

        i = max(es) + 1 if es else 1

        ret = -1
        ion = self.scan_manager.ion_optics_manager

        self._peak_center_start_hook()
        time.sleep(2)
        name = "Peak Center {:02d}".format(i)
        if ion.setup_peak_center(new=True, **setup_kw):
            self._on_peak_center_start()

            invoke_in_main_thread(
                self._open_editor, PeakCenterEditor(model=ion.peak_center, name=name)
            )

            ion.do_peak_center(**peak_kw)

            ret = ion.peak_center_result

        self._peak_center_stop_hook()
        return ret

    def _peak_center_start_hook(self):
        pass

    def _peak_center_stop_hook(self):
        pass

    def _scan_factory(self):
        sim = self.scan_manager.spectrometer.simulation
        name = "Scan (Simulation)" if sim else "Scan"
        # self._open_editor(ScanEditor(model=self.scan_manager, name=name))
        # print 'asdfas', self.editor_area.control
        # print [e for e in self.editor_area.control.children() if isinstance(e, EditorWidget)]
        # super(SpectrometerTask, self).activated()

        se = ScanEditor(model=self.scan_manager, name=name)
        self._open_editor(se)

    def _default_layout_default(self):
        return TaskLayout(
            left=Splitter(
                PaneItem("pychron.spectrometer.controls"), orientation="vertical"
            ),
            right=VSplitter(
                PaneItem("pychron.spectrometer.intensities"),
                # PaneItem("pychron.spectrometer.readout"),
            ),
        )

        # def create_central_pane(self):

        # g = ScanPane(model=self.scan_manager)
        # return g

    @on_trait_change("scan_manager:mass_scanner:new_scanner")
    def _handle_mass_scan_event(self):
        self._scan_event(self.scan_manager.mass_scanner)

    @on_trait_change("scan_manager:dac_scanner:new_scanner")
    def _handle_dac_scan_event(self):
        self._scan_event(self.scan_manager.dac_scanner)

    def _scan_event(self, scanner):
        sim = self.scan_manager.spectrometer.simulation
        name = "Magnet Scan (Simulation)" if sim else "Magnet Scan"

        editor = next(
            (e for e in self.editor_area.editors if e.id == "pychron.scanner"), None
        )
        if editor is not None:
            scanner.reset()
        else:
            editor = ScannerEditor(model=scanner, name=name, id="pychron.scanner")
            self._open_editor(editor, activate=False)
            self.split_editors(0, 1, h2=300, orientation="vertical")

        self.activate_editor(editor)

    @on_trait_change("window:opened")
    def _opened(self):
        self.scan_manager.activate()

        self._scan_factory()
        # ee = [
        #     e
        #     for e in self.editor_area.control.children()
        #     if isinstance(e, EditorWidget)
        # ][0]
        # print int(ee.features())
        # ee.setFeatures(QtGui.QDockWidget.NoDockWidgetFeatures)
        # print int(ee.features())
        # ee.update_title()


# ============= EOF =============================================
