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
from envisage.ui.tasks.preferences_pane import PreferencesPane
from traits.api import Str, Bool, Int
from traitsui.api import View, Item, HGroup, VGroup

from pychron.core.helpers.strtools import to_bool
from pychron.core.pychron_traits import BorderVGroup
from pychron.database.tasks.connection_preferences import (
    ConnectionPreferences,
    ConnectionPreferencesPane,
    ConnectionFavoriteItem,
)
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper


class DVCConnectionItem(ConnectionFavoriteItem):
    organization = Str
    meta_repo_name = Str
    meta_repo_dir = Str
    repository_root = Str
    attributes = (
        "name",
        "kind",
        "username",
        "host",
        "dbname",
        "password",
        "enabled",
        "default",
        "path",
        "organization",
        "meta_repo_name",
        "meta_repo_dir",
        "timeout",
        "repository_root",
    )

    def __init__(self, schema_identifier="", attrs=None, load_names=False):
        super(ConnectionFavoriteItem, self).__init__()
        self.schema_identifier = schema_identifier

        if attrs:
            attrs = attrs.split(",")
            try:
                (
                    self.name,
                    self.kind,
                    self.username,
                    self.host,
                    self.dbname,
                    self.password,
                    enabled,
                    default,
                    path,
                ) = attrs

            except ValueError:
                try:
                    (
                        self.name,
                        self.kind,
                        self.username,
                        self.host,
                        self.dbname,
                        self.password,
                        enabled,
                        default,
                        self.path,
                        self.organization,
                        self.meta_repo_name,
                        self.meta_repo_dir,
                    ) = attrs
                except ValueError:
                    try:
                        (
                            self.name,
                            self.kind,
                            self.username,
                            self.host,
                            self.dbname,
                            self.password,
                            enabled,
                            default,
                            self.path,
                            self.organization,
                            self.meta_repo_name,
                            self.meta_repo_dir,
                            timeout,
                        ) = attrs
                        self.timeout = int(timeout)
                    except ValueError:
                        (
                            self.name,
                            self.kind,
                            self.username,
                            self.host,
                            self.dbname,
                            self.password,
                            enabled,
                            default,
                            self.path,
                            self.organization,
                            self.meta_repo_name,
                            self.meta_repo_dir,
                            timeout,
                            self.repository_root,
                        ) = attrs
                        self.timeout = int(timeout)

            self.enabled = to_bool(enabled)
            self.default = to_bool(default)
            if load_names:
                self.load_names()


class DVCConnectionPreferences(ConnectionPreferences):
    preferences_path = "pychron.dvc.connection"
    _adapter_klass = "pychron.dvc.dvc_database.DVCDatabase"
    _schema_identifier = "AnalysisTbl"
    _fav_klass = DVCConnectionItem


class DVCConnectionPreferencesPane(ConnectionPreferencesPane):
    model_factory = DVCConnectionPreferences
    category = "DVC"

    def traits_view(self):
        ev = View(
            Item("organization"),
            Item("meta_repo_name", label="MetaData Name"),
            Item("meta_repo_dir", label="MetaData Directory"),
            Item("repository_root", label="Repository Directory"),
        )
        fav_grp = self.get_fav_group(edit_view=ev)

        return View(fav_grp)


class DVCPreferences(BasePreferencesHelper):
    preferences_path = "pychron.dvc"
    use_cocktail_irradiation = Bool
    use_cache = Bool
    max_cache_size = Int
    update_currents_enabled = Bool
    use_auto_pull = Bool(True)
    use_auto_push = Bool(False)
    use_default_commit_author = Bool(False)


class DVCPreferencesPane(PreferencesPane):
    model_factory = DVCPreferences
    category = "DVC"

    def traits_view(self):
        v = View(
            VGroup(
                BorderVGroup(
                    Item(
                        "use_cocktail_irradiation",
                        tooltip="Use the special cocktail.json for defining the "
                        "irradiation flux and chronology",
                        label="Use Cocktail Irradiation",
                    )
                ),
                BorderVGroup(
                    Item(
                        "use_auto_pull",
                        label="Auto Pull",
                        tooltip="If selected, automatically "
                        "update your version to the "
                        "latest version. Deselect if "
                        "you want to be asked to pull "
                        "the official version.",
                    ),
                    Item(
                        "use_auto_push",
                        label="Auto Push",
                        tooltip="Push changes when a PushNode is used automatically without asking "
                        "for confirmation.",
                    ),
                ),
                BorderVGroup(
                    Item(
                        "use_default_commit_author", label="Use Default Commit Author"
                    ),
                    label="Commit",
                ),
                BorderVGroup(
                    Item("update_currents_enabled", label="Enabled"),
                    label="Current Values",
                ),
                BorderVGroup(
                    HGroup(
                        Item("use_cache", label="Enabled"),
                        Item("max_cache_size", label="Max Size"),
                    ),
                    label="Cache",
                ),
            )
        )
        return v


class DVCExperimentPreferences(BasePreferencesHelper):
    preferences_path = "pychron.dvc.experiment"
    use_dvc_persistence = Bool
    dvc_save_timeout_minutes = Int
    use_dvc_overlap_save = Bool


class DVCExperimentPreferencesPane(PreferencesPane):
    model_factory = DVCExperimentPreferences
    category = "Experiment"

    def traits_view(self):
        v = View(
            BorderVGroup(
                Item("use_dvc_persistence", label="Use DVC Persistence"),
                Item("use_dvc_overlap_save", label="Use DVC Overlap Save"),
                Item(
                    "dvc_save_timeout_minutes",
                    label="DVC Save timeout (minutes)",
                    enabled_when="use_dvc_overlap_save",
                ),
                label="DVC",
            )
        )
        return v


class DVCRepositoryPreferences(BasePreferencesHelper):
    preferences_path = "pychron.dvc.repository"
    check_for_changes = Bool
    auto_fetch = Bool


class DVCRepositoryPreferencesPane(PreferencesPane):
    model_factory = DVCRepositoryPreferences
    category = "Repositories"

    def traits_view(self):
        v = View(
            BorderVGroup(
                Item("check_for_changes", label="Check for Changes"),
                Item(
                    "auto_fetch",
                    label="Auto Fetch",
                    tooltip='Automatically "fetch" when a local repository is selected. Turn this off '
                    "if fetching speed is an issue",
                ),
                label="",
            )
        )
        return v


# ============= EOF =============================================
