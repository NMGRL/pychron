import os

from pyface.constant import OK
from pyface.directory_dialog import DirectoryDialog
from traits.api import Button, List, Property, Str
from traitsui.api import HGroup, Item, UItem, VGroup

from pychron.cli_profiles import available_profile_names
from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.ui.check_list_editor import CheckListEditor
from pychron.install_bootstrap import bootstrap_runtime_root
from pychron.install_validation import build_runtime_validation_report
from pychron.loggable import Loggable
from pychron.starter_bundles import available_bundle_names


class FirstRunWizard(Loggable):
    root = Str
    browse = Button("Browse")
    selected_bundles = List(Str)
    selected_profiles = List(Str)
    available_bundles = Property
    available_profiles = Property

    def run_bootstrap(self):
        root, _, merged = bootstrap_runtime_root(
            self.root,
            profiles=self.selected_profiles,
            bundles=self.selected_bundles,
        )
        report = build_runtime_validation_report(
            root,
            profiles=merged.requested,
            bundles=self.selected_bundles,
        )
        return root, merged, report

    def _browse_fired(self):
        dialog = DirectoryDialog(
            action="open",
            default_path=os.path.expanduser(self.root),
        )
        if dialog.open() == OK and dialog.path:
            self.root = dialog.path

    def _get_available_bundles(self):
        return list(available_bundle_names())

    def _get_available_profiles(self):
        return list(available_profile_names())

    def traits_view(self):
        return okcancel_view(
            VGroup(
                HGroup(
                    Item("root", label="Pychron Root"),
                    UItem("browse"),
                ),
                UItem(
                    "selected_bundles",
                    style="custom",
                    editor=CheckListEditor(name="available_bundles", cols=2),
                ),
                UItem(
                    "selected_profiles",
                    style="custom",
                    editor=CheckListEditor(name="available_profiles", cols=3),
                ),
            ),
            title="Pychron First-Run Setup",
            width=600,
        )
