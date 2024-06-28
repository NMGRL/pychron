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
import os

# ============= enthought library imports =======================
from pyface.message_dialog import information
from traits.api import Str, Instance
from traitsui.api import Item, HGroup, EnumEditor, View, VGroup, UItem
from traitsui.editors.api import DirectoryEditor
from uncertainties import ufloat, std_dev, nominal_value

from pychron.base_fs import BaseFS
from pychron.core.confirmation import confirmation_dialog
from pychron.core.helpers.filetools import unique_path2, add_extension
from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.progress import progress_iterator, progress_loader
from pychron.dvc import dvc_dump
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.options.options_manager import OptionsController
from pychron.paths import paths
from pychron.pipeline.editors.set_ia_editor import SetInterpretedAgeEditor
from pychron.pipeline.nodes.base import BaseNode
from pychron.pipeline.nodes.data import BaseDVCNode
from pychron.pipeline.tables.table_options_manager import TableOptionsManager
from pychron.pipeline.tables.xlsx_table_writer import XLSXAnalysisTableWriter


class PersistNode(BaseDVCNode):
    def configure(self, **kw):
        return True


class FileNode(PersistNode):
    root = Str
    extension = ""


class PDFNode(FileNode):
    extension = ".pdf"


class PDFFigureNode(PDFNode):
    name = "PDF Figure"

    def configure(self, **kw):
        return BaseNode.configure(self, **kw)

    def traits_view(self):
        return self._view_factory(
            Item("root", editor=DirectoryEditor(root_path=paths.data_dir)), width=500
        )

    def _generate_path(self, ei):
        name = ei.name.replace(" ", "_")

        p, _ = unique_path2(self.root, name, extension=self.extension)
        return p

    def run(self, state):
        for ei in state.editors:
            if hasattr(ei, "save_file"):
                print("save file to", self._generate_path(ei))
                ei.save_file(self._generate_path(ei))


class DVCPersistNode(PersistNode):
    dvc = Instance("pychron.dvc.dvc.DVC")
    commit_message = Str
    commit_tag = Str
    modifier = Str

    # def __init__(self, *args, **kwargs):
    #     super(DVCPersistNode, self).__init__(*args, **kwargs)

    def _persist(self, state, msg):
        mods = self.modifier
        if not isinstance(mods, tuple):
            mods = (self.modifier,)

        modp = []
        for mi in mods:
            modpi = self.dvc.update_analyses(
                state.unknowns, mi, "<{}>.{} {}".format(self.commit_tag, mi, msg)
            )
            modp.extend(modpi)

        if modp:
            state.modified = True
            for m in modp:
                state.modified_projects = state.modified_projects.union(m)


class DefineEquilibrationPersistNode(DVCPersistNode):
    name = "Save Equilibration"

    def run(self, state):
        if not state.saveable_keys:
            return

        def wrapper(x, prog, i, n):
            return self._save_eq(x, prog, i, n, state.saveable_keys)

        msg = ",".join(
            "{}({})".format(*a) for a in zip(state.saveable_keys, state.saveable_fits)
        )
        items = progress_loader(state.unknowns, wrapper, threshold=1, unpack=False)

        author = self.dvc.get_author()
        modpis = self.dvc.update_analysis_paths(
            items, "<DEFINE EQUIL> {}".format(msg), author
        )
        modpps = self.dvc.update_analyses(
            state.unknowns, "intercepts", "<ISOEVO> modified by DEFINE EQUIL", author
        )
        modpis.extend(modpps)

        if modpis:
            state.modified = True
            state.modified_projects = state.modified_projects.union(modpis)

    def _save_eq(self, x, prog, i, n, keys):
        if prog:
            prog.change_message("Save Equilibration {} {}/{}".format(x.record_id, i, n))

        path = self.dvc.save_defined_equilibration(x, keys)
        self.dvc.save_fits(x, keys)
        return x, path


class IsotopeEvolutionPersistNode(DVCPersistNode):
    name = "Save Iso Evo"
    commit_tag = "ISOEVO"
    modifier = ("intercepts", "baselines")
    classifier_db = Instance(
        "pychron.classifier.database_adapter.ArgonIntelligenceDatabase"
    )

    def run(self, state):
        if not state.saveable_keys:
            return

        if self.classifier_db:
            self.classifier_db.connect()
            self.classifier_db.create_session()

        def wrapper(x, prog, i, n):
            self._save_fit(x, prog, i, n, state.saveable_keys)

        progress_iterator(state.unknowns, wrapper, threshold=1)

        msg = self.commit_message
        if not msg:
            f = ",".join(
                "{}({})".format(x, y)
                for x, y in zip(state.saveable_keys, state.saveable_fits)
            )
            msg = "fits={}".format(f)

        self._persist(state, msg)
        if self.classifier_db:
            self.classifier_db.close_session()

    def _save_fit(self, x, prog, i, n, keys):
        if prog:
            prog.change_message("Save Fits {} {}/{}".format(x.record_id, i, n))

        self.dvc.save_fits(x, keys)
        if self.classifier_db:
            for k in keys:
                self.classifier_db.add_classification(x, k)


class BlanksPersistNode(DVCPersistNode):
    name = "Save Blanks"
    commit_tag = "BLANKS"
    modifier = "blanks"

    def run(self, state):
        # if not state.user_review:
        # for ai in state.unknowns:
        #     self.dvc.save_blanks(ai, state.saveable_keys, state.references)
        wrapper = lambda x, prog, i, n: self._save_blanks(
            x, prog, i, n, state.saveable_keys, state.references
        )
        progress_iterator(state.unknowns, wrapper, threshold=1)
        msg = self.commit_message
        if not msg:
            f = ",".join(
                "{}({})".format(x, y)
                for x, y in zip(state.saveable_keys, state.saveable_fits)
            )
            msg = "auto update blanks, fits={}".format(f)

        self._persist(state, msg)

    def _save_blanks(self, ai, prog, i, n, saveable_keys, references):
        if prog:
            prog.change_message("Save Blanks {} {}/{}".format(ai.record_id, i, n))
        # print 'sssss', saveable_keys
        self.dvc.save_blanks(ai, saveable_keys, references)


class ICFactorPersistNode(DVCPersistNode):
    name = "Save ICFactor"
    commit_tag = "ICFactor"
    modifier = "icfactors"

    def run(self, state):
        wrapper = lambda ai, prog, i, n: self._save_icfactors(ai, prog, i, n, state)
        progress_iterator(state.unknowns, wrapper, threshold=1)

        if state.use_source_correction:
            msg = "source correction ic_factors"
        else:
            msg = self.commit_message
            if not msg:
                f = ",".join(
                    "{}({})".format(x, y)
                    for x, y in zip(state.saveable_keys, state.saveable_fits)
                )
                msg = "auto update ic_factors, fits={}".format(f)

        self._persist(state, msg)

    def _save_icfactors(self, ai, prog, i, n, state):
        if prog:
            prog.change_message(
                "Save IC Factor for {} {}/{}".format(ai.record_id, i, n)
            )

        if state.delete_existing_icfactors:
            self.dvc.delete_existing_icfactors(ai, state.saveable_keys)

        self.dvc.save_icfactors(
            ai,
            state.saveable_keys,
            state.saveable_fits,
            state.references,
            state.use_source_correction,
            state.standard_ratios,
            state.reference_data,
        )


class FluxPersistNode(DVCPersistNode):
    name = "Save Flux"
    commit_tag = "FLUX"

    def run(self, state):
        if state.monitor_positions:
            meta_repo = self.dvc.meta_repo
            meta_repo.smart_pull(quiet=False)
            xs = [
                xi
                for xi in state.monitor_positions + state.unknown_positions
                if xi.save
            ]

            level_obj, p = self.dvc.meta_repo.get_level_obj(
                state.irradiation, state.level
            )

            po = state.flux_options
            options = dict(
                model_kind=po.model_kind,
                predicted_j_error_type=po.predicted_j_error_type,
                use_weighted_fit=po.use_weighted_fit,
                interpolation_style=po.interpolation_style,
                monte_carlo_ntrials=po.monte_carlo_ntrials,
                use_monte_carlo=po.use_monte_carlo,
                monitor_name=po.monitor_name,
                monitor_age=po.monitor_age,
                monitor_material=po.monitor_name,
                monitor_reference=po.selected_monitor,
            )

            lk = po.lambda_k
            decay_constants = {
                "lambda_k_total": nominal_value(lk),
                "lambda_k_total_error": std_dev(lk),
            }

            def update(irp, prog, i, n):
                if prog:
                    prog.change_message(
                        "Save J for {} {}/{}".format(irp.identifier, i, n)
                    )

                irradiation = irp.irradiation
                level = irp.level
                pos = irp.hole_id
                identifier = irp.identifier
                j = irp.j
                e = irp.jerr
                mj = irp.mean_j
                me = irp.mean_jerr
                analyses = irp.analyses
                position_jerr = irp.position_jerr
                mmswd = irp.mean_j_mswd

                meta_repo.update_flux(
                    irradiation,
                    level,
                    pos,
                    identifier,
                    j,
                    e,
                    mj,
                    me,
                    mmswd,
                    decay=decay_constants,
                    analyses=analyses,
                    options=options,
                    add=False,
                    position_jerr=position_jerr,
                    save_predicted=irp.save_predicted,
                    jd=level_obj,
                )

                uj = ufloat(j, e, tag="j")
                for i in state.unknowns:
                    if i.identifier == irp.identifier:
                        i.j = uj
                        i.arar_constants.lambda_k = lk
                        i.recalculate_age()

            progress_iterator(
                xs,
                update,
                # lambda *args: self._save_j(state, level_obj, p, *args),
                threshold=1,
            )

            dvc_dump(level_obj, p)

            meta_repo.add(p, commit=False)
            self.dvc.meta_commit(
                "fit flux for {}{}".format(state.irradiation, state.level)
            )

            if confirmation_dialog("Would you like to share your changes?"):
                self.dvc.meta_repo.smart_pull()
                self.dvc.meta_repo.push()


class XLSXAnalysisTablePersistNode(BaseDVCNode):
    name = "Excel Analysis Table"
    # auto_configure = False
    # configurable = False

    # options_klass = XLSXAnalysisTableWriterOptions
    options_klass = TableOptionsManager
    options_view = Instance(View)

    def configure(self, refresh=True, pre_run=False, **kw):
        if not pre_run:
            self._manual_configured = True

        self._configure_hook()
        info = OptionsController(model=self.options).edit_traits(
            view=self.options_view, kind="livemodal"
        )
        if info.result:
            if self.options.selected_options:
                self.options.selected_options.overwrite = False
                p = self.options.selected_options.get_path()
                if os.path.isfile(p):
                    if confirmation_dialog(
                        "File {} already exists. Would you like to overwrite it?".format(
                            p
                        )
                    ):
                        self.options.selected_options.overwrite = True
                return True

    def _pre_run_hook(self, state):
        if state.unknowns:
            ri = tuple({ai.repository_identifier for ai in state.unknowns})
            options = self.options.selected_options
            if options:
                if not options.root_name:
                    options.root_name = ri[0]

    def _finish_configure(self):
        self.options.dump()

    def run(self, state):
        if state.unknowns and state.run_groups:
            writer = XLSXAnalysisTableWriter()
            if not self.options.selected_options.use_sample_metadata_saved_with_run:
                for gi in state.run_groups.get("unknowns", []):
                    self.dvc.sync_ia_metadata(gi)

            writer.build(state.run_groups, options=self.options.selected_options)

    def _options_view_default(self):
        agrp = HGroup(
            Item(
                "selected",
                show_label=False,
                editor=EnumEditor(name="names"),
                tooltip="List of available plot options",
            ),
            icon_button_editor(
                "controller.save_options", "disk", tooltip="Save changes to options"
            ),
            icon_button_editor(
                "controller.save_as_options",
                "save_as",
                tooltip="Save options with a new name",
            ),
            icon_button_editor(
                "controller.add_options", "add", tooltip="Add new plot options"
            ),
            icon_button_editor(
                "controller.delete_options",
                "delete",
                tooltip="Delete current plot options",
                enabled_when="delete_enabled",
            ),
            icon_button_editor(
                "controller.factory_default",
                "edit-bomb",
                enabled_when="selected",
                tooltip="Apply factory defaults",
            ),
        )

        return okcancel_view(
            VGroup(agrp, UItem("selected_options", style="custom")),
            title="XLS Table Options",
            height=0.75,
            width=0.75,
            resizable=True,
        )


class InterpretedAgePersistNode(BaseDVCNode):
    name = "Save Interpreted Ages"
    configurable = False

    def run(self, state):
        dvc = self.dvc
        for e in state.editors:
            if isinstance(e, SetInterpretedAgeEditor):
                for ia in e.groups:
                    if ia.use:
                        dvc.add_interpreted_age(ia)


class CosmogenicCorrectionPersistNode(DVCPersistNode):
    name = "Save Cosmogenic Correction"

    def run(self, state):
        self.dvc.save_cosmogenic_correction(state.unknowns)


class FluxMonitorMeansPersistNode(BaseNode):
    configurable = False
    name = "Save Flux CSV"

    def run(self, state):
        b = BaseFS()

        p = b.save_file_dialog(
            default_filename="{}{}_flux.csv".format(state.irradiation, state.level),
            default_directory=paths.data_dir,
        )
        if p:
            p = add_extension(p, ".csv")
            with open(p, "w") as wfile:
                header = (
                    "identifier,irradiation,level,sample,hole_id,"
                    "saved_j,saved_jerr,mean_j,mean_jerr,mean_j_mswd,model_kind,x,y"
                )
                attrs = header.split(",")
                wfile.write("{}\n".format(header))
                for mp in state.monitor_positions:
                    line = ",".join([str(getattr(mp, attr)) for attr in attrs])
                    wfile.write("{}\n".format(line))

            information(None, "Flux saved to\n\n{}".format(p))


# class TablePersistNode(FileNode):
#     pass
#
#
# class XLSTablePersistNode(BaseNode):
#     name = 'Save Analysis Table'
#     options_klass = AnalysisTablePersistOptionsView
#
#     def _options_factory(self):
#         opt = AnalysisTablePersistOptions(name='foo')
#         return self.options_klass(model=opt)
#
#     def run(self, state):
#         from pychron.pipeline.editors.arar_table_editor import ArArTableEditor
#
#         for editor in state.editors:
#             if isinstance(editor, ArArTableEditor):
#                 opt = self.options.model
#                 if opt.extension == 'xls':
#                     editor.make_xls_table(opt)
#                     view_file(opt.path)
#
#                     # basename = 'test_xls_table'
#                     # path, _ = unique_path2(paths.data_dir, basename, extension='.xls')
#                     # editor.make_xls_table('FooBar', path)
#
#
#
# class SetInterpretedAgeNode(BaseDVCNode):
#     name = 'Set IA'
#
#     def configure(self, pre_run=False, **kw):
#         return True
#
#     def run(self, state):
#         for editor in state.editors:
#             if isinstance(editor, InterpretedAgeEditor):
#                 ias = editor.get_interpreted_ages()
#                 set_interpreted_age(self.dvc, ias)
#
#
# class InterpretedAgeTablePersistNode(BaseNode):
#     name = 'Save IA Table'
#     options_klass = InterpretedAgePersistOptionsView
#
#     def _options_factory(self):
#         opt = InterpretedAgePersistOptions(name='foo')
#         return self.options_klass(model=opt)
#
#     def run(self, state):
#         from pychron.pipeline.editors.interpreted_age_table_editor import InterpretedAgeTableEditor
#         for editor in state.editors:
#             if isinstance(editor, InterpretedAgeTableEditor):
#                 opt = self.options.model
#                 if opt.extension == 'xlsx':
#                     editor.make_xls_table(opt)
#                     view_file(opt.path)

# ============= EOF =============================================
