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
import os

from apptools.preferences.preference_binding import bind_preference
from traits.api import Any, on_trait_change, Date, Time, Instance, Bool, Str

from pychron.envisage.browser.interpreted_age_recall_editor import (
    InterpretedAgeRecallEditor,
)
from pychron.envisage.browser.recall_editor import RecallEditor
from pychron.envisage.browser.recall_table_configurer import RecallTableConfigurer
from pychron.envisage.tasks.editor_task import BaseEditorTask
from pychron.envisage.view_util import open_view
from pychron.paths import paths
from pychron.processing.analyses.view.adapters import (
    IsotopeTabularAdapter,
    IntermediateTabularAdapter,
)
from pychron.processing.analyses.view.edit_analysis_view import AnalysisEditView

"""
add toolbar action to open another editor tab


"""

"""
@todo: how to fit cocktail/air blanks. make special project called references.
added sample to air, cocktail. added samples to references project
"""

DEFAULT_SPEC = "Spectrometer"
DEFAULT_AT = "Analysis Type"
DEFAULT_ED = "Extraction Device"


def unique_list(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x.name in seen or seen_add(x.name))]


def listify(records):
    if not isinstance(records, (list, tuple)):
        records = [records]
    elif isinstance(records, tuple):
        records = list(records)
    return records


class BaseBrowserTask(BaseEditorTask):
    default_task_name = "Recall"
    browser_model = Instance(
        "pychron.envisage.browser.base_browser_model.BaseBrowserModel"
    )
    interpreted_age_browser_model = Instance(
        "pychron.envisage.browser."
        "interpreted_age_browser_model.InterpretedAgeBrowserModel"
    )
    dvc = Instance("pychron.dvc.dvc.DVC")

    isotope_adapter = Instance(IsotopeTabularAdapter, ())
    intermediate_adapter = Instance(IntermediateTabularAdapter, ())
    recall_configurer = Instance(RecallTableConfigurer)

    start_date = Date
    start_time = Time

    end_date = Date
    end_time = Time

    browser_pane = Any
    diff_enabled = Bool

    mounted_media_root = Str

    _activated = False
    _top_level_filter = None
    _append_replace_analyses_enabled = True

    def __init__(self, *args, **kw):
        super(BaseBrowserTask, self).__init__(*args, **kw)
        bind_preference(
            self, "mounted_media_root", "pychron.browser.mounted_media_root"
        )

    def prepare_destroy(self):
        if self.browser_model:
            self.browser_model.dump_browser()
            self._activated = False

            self._destroy_browser_model()

    def activated(self):
        if self.application.get_plugin("pychron.mass_spec.plugin"):
            self.diff_enabled = True

    def edit_analysis(self):
        self.debug("Edit analysis data")
        if not self.has_active_editor():
            return

        editor = self.active_editor
        if not isinstance(editor, RecallEditor):
            self.warning_dialog("Active tab must be a Recall tab")
            return

        if (
            hasattr(editor, "edit_view")
            and editor.edit_view
            and editor.edit_view.control
        ):
            editor.edit_view.show()
        else:

            e = AnalysisEditView(editor, dvc=self.dvc)
            info = open_view(e)
            # info = e.edit_traits()
            e.control = info.control
            editor.edit_view = e

    def play_analysis_video(self, records=None):
        try:
            from pychron.image.video_player import VideoPlayer
        except ImportError:
            self.warning_dialog(
                "Failed setting up VideoPlayer. Please verify python-vlc is installed"
            )
            return

        if records is None:
            if not self.has_active_editor(klass=RecallEditor):
                return
            r = self.active_editor.analysis

        else:
            records = listify(records)
            r = records[0]

        # find video
        rid = r.record_id
        load = r.load_name
        subdirname = "FusionsCO2"
        name = "{}-001.avi".format(rid)
        lp = os.path.join(paths.video_dir, name)
        if not os.path.isfile(lp):
            # check our mounted media directory
            d = self.mounted_media_root
            if d and os.path.isdir(d):
                mp = os.path.join(d, subdirname, load, name)
                if os.path.isfile(mp):
                    lp = mp

            if not os.path.isfile(lp):
                # use MediaStorage to grab data
                msm = self.application.get_service(
                    "pychron.media_storage.manager.MediaStorageManager"
                )
                if not msm:
                    self.warning_dialog(
                        "Media Storage Plugin is required. Please enable and try again"
                    )
                    return

                rp = os.path.join(subdirname, load, name)
                self.debug("looking for path={}".format(rp))
                if msm.exists(rp):
                    msm.get(rp, lp)

        if os.path.isfile(lp):
            vp = VideoPlayer(video_path=lp, title=name)
            vp.edit_traits()
        else:
            self.information_dialog("No Video available for {}".format(rid))

    def recall(self, records, open_copy=False, use_quick=True):
        """
        if analysis is already open activate the editor
        otherwise open a new editor

        if open_copy is True, allow multiple instances of the same analysis
        """
        records = listify(records)

        for ri in records:
            try:
                rid = ri.record_id
            except AttributeError:
                rid = ""
            self.debug("recall {} {}".format(rid, ri))

        if not open_copy:
            records = self._open_existing_recall_editors(records)
            if records:
                pf = None
                if self.browser_model.use_quick_recall:
                    pf = 60

                try:
                    records = self.dvc.make_analyses(
                        records, pull_frequency=pf, use_progress=False
                    )
                except BaseException:
                    records = None
                    self.debug_exception()

        if records:
            self._open_recall_editors(records, use_quick=use_quick)
        else:
            self.warning_dialog(
                "Failed to recall the requested analyses. Please check the log for more details"
            )

    def interpreted_age_recall(self, record):
        existing = [e.basename for e in self.get_editors(InterpretedAgeRecallEditor)]

        items = self.dvc.make_interpreted_ages(record)
        for item in items:
            editor = InterpretedAgeRecallEditor(item)
            if existing and editor.basename in existing:
                editor.instance_id = existing.count(editor.basename)

            editor.set_name(item.name)
            self._open_editor(editor)

    def configure_recall(self):
        self.debug("configure recall")
        tc = self.recall_configurer
        info = tc.edit_traits()
        if info.result:

            self._set_adapter_sig_figs()

            editors = self.get_recall_editors()
            for e in editors:
                e.analysis_view.show_intermediate = tc.show_intermediate
                e.analysis_view.main_view.set_options(
                    e.analysis, self.recall_configurer.recall_options
                )
                tc.set_fonts(e.analysis_view)

            # for e in self.get_recall_editors():

    def configure_sample_table(self):
        self.debug("configure sample table")
        bm = self.browser_model
        bm.configure_sample_table()

    def configure_analyses_table(self):
        self.debug("configure analyses table")
        at = self.browser_model.table
        at.configure_table()

    def load_review_status(self):
        self.debug("load review status")
        self.browser_model.load_review_status()

    def get_recall_editors(self):
        es = self.editor_area.editors
        return [e for e in es if isinstance(e, RecallEditor)]

    def show_extraction_graph(self):
        if not self.has_active_editor(klass=RecallEditor):
            return

        from pychron.graph.stacked_graph import StackedGraph
        from numpy import array
        import struct
        import base64

        an = self.active_editor.analysis
        data = an.get_extraction_data()

        def extract_blob(blob):
            blob = base64.b64decode(blob)
            if blob != "No Response":
                x, y = array(
                    [
                        struct.unpack("<ff", blob[i : i + 8])
                        for i in range(0, len(blob), 8)
                    ]
                ).T
                x[0] = 0
            else:
                x, y = [], []

            return x, y

        g = StackedGraph()
        g.window_title = "Extraction Results - {}".format(an.record_id)
        g.new_plot(padding=[70, 10, 10, 60])

        xx, yy = extract_blob(data["request"])
        g.new_series(xx, yy, plotid=0)
        g.set_y_limits(pad="0.1")

        g.new_plot(padding=[70, 10, 10, 10])
        xx, yy = extract_blob(data["response"])
        g.new_series(xx, yy, plotid=1)

        g.set_y_title("Temp (C)", plotid=0)
        g.set_x_title("Time (s)", plotid=0)
        g.set_y_title("% Output", plotid=1)
        open_view(g)

    # private
    def _opened_hook(self):
        if self.dvc:
            self.dvc.initialize()
            self.dvc.create_session()
        if not self.browser_model.is_activated:
            self._setup_browser_model()
        else:
            # reattach DVCIsotopeRecordViews to the session
            self.browser_model.reattach()

    def _closed_hook(self):
        self.dvc.clear_pull_cache()
        self.dvc.close_session()

    def _get_editor_by_uuid(self, uuid):
        return next(
            (
                editor
                for editor in self.editor_area.editors
                if isinstance(editor, RecallEditor)
                and editor.model
                and editor.model.uuid == uuid
            ),
            None,
        )

    def _open_existing_recall_editors(self, records):
        editor = None
        # check if record already is open
        for r in records:

            editor = self._get_editor_by_uuid(r.uuid)
            if editor:
                records.remove(r)

        # activate editor if open
        if editor:
            self.activate_editor(editor)
        return records

    def _setup_browser_model(self):
        model = self.browser_model
        model.pattributes += ("irradiation_enabled", "use_focus_switching")

    def _destroy_browser_model(self):
        pass

    def _activate_sample_browser(self):
        self.browser_model.activate_browser()
        self._activated = True

    def _get_selected_analyses(self, **kw):
        """ """
        ret = self.browser_model.get_selection(
            low_post=self.start_date, high_post=self.end_date, **kw
        )
        return ret

    def _get_browser_model(self):
        model = self.application.get_service(
            "pychron.processing.tasks.browser.browser_model.BrowserModel"
        )
        self.debug("Browser model model={}, id={}".format(model, id(model)))
        return model

    def _set_selected_analysis(self, new):
        pass

    def _selector_dclick(self, item):
        pass

    def _graphical_filter_hook(self, ans, is_append):
        pass

    def _set_adapter_sig_figs(self):
        self.isotope_adapter.sig_figs = (
            self.recall_configurer.recall_options.isotope_sig_figs
        )
        self.intermediate_adapter.sig_figs = (
            self.recall_configurer.recall_options.intermediate_sig_figs
        )

    def _open_recall_editors(self, ans, use_quick=True):
        self._set_adapter_sig_figs()

        existing = [e.basename for e in self.get_recall_editors()]
        if ans:
            quick = self.browser_model.use_quick_recall and use_quick
            for rec in ans:

                av = rec.analysis_view_factory(quick=False)
                av.isotope_view.isotope_adapter = self.isotope_adapter
                av.isotope_view.intermediate_adapter = self.intermediate_adapter
                av.isotope_view.show_intermediate = (
                    self.recall_configurer.show_intermediate
                )

                self.recall_configurer.set_fonts(av)
                av.main_view.set_options(rec, self.recall_configurer.recall_options)
                av.dvc = self.dvc
                if quick:
                    editor = self.browser_model.recall_editor
                    if not editor:
                        editor = RecallEditor(rec, av)
                        self.browser_model.recall_editor = editor
                    else:
                        editor.init(rec, av)
                    editor.set_name(editor.basename)
                    break
                else:
                    editor = RecallEditor(rec, av)

                    # editor.analysis_view = av
                    # editor.basename = rec.record_id
                    if existing and editor.basename in existing:
                        editor.instance_id = existing.count(editor.basename)
                    editor.set_name(editor.basename)

                    self._open_editor(editor, activate=False)

        else:
            self.warning("could not load records")

    # @on_trait_change('browser_model:[table:context_menu_event, time_view_model:context_menu_event]')
    @on_trait_change("browser_model:table:context_menu_event")
    def _handle_analysis_table_context_menu(self, new):
        if new:
            sel = self.browser_model.table.selected

            action, modifiers = new
            # if action in ('append', 'replace'):
            #     self._append_replace_unknowns(action == 'append')
            if action == "open":
                if sel:
                    open_copy = False
                    if modifiers:
                        open_copy = modifiers.get("open_copy")

                    for it in sel:
                        self.recall(it, open_copy=open_copy)

    @on_trait_change("interpreted_age_browser_model:[table:dclicked]")
    def _handle_ia_dclicked(self, new):
        if new:
            try:
                self.interpreted_age_recall(new.item)
            except BaseException as e:
                import traceback

                traceback.print_exc()
                self.critical("interpeted_age_table:dclicked error {}".format(str(e)))

    @on_trait_change("browser_model:[table:key_pressed]")
    def _handle_key_pressed(self, new):
        if new and new.control:
            d = None
            if new.is_key("N"):
                d = 1
            elif new.is_key("B"):
                d = -1

            if d:
                item = self.browser_model.table.increment_selected(d)
                self.recall(item)

    @on_trait_change("browser_model:[table:dclicked]")
    def _handle_dclicked(self, new):
        if new:
            try:
                self.recall(new.item)
            except BaseException as e:
                import traceback

                traceback.print_exc()
                self.critical("table:dclicked error {}".format(str(e)))

    def _dclicked_sample_hook(self):
        pass

    def _recall_configurer_default(self):
        rc = RecallTableConfigurer()
        rc.intermediate_table_configurer.set_adapter(self.intermediate_adapter)
        rc.isotope_table_configurer.set_adapter(self.isotope_adapter)
        rc.load()
        return rc


# ============= EOF =============================================
