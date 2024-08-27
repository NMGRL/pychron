# ===============================================================================
# Copyright 2012 Jake Ross
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

# ============= standard library imports ========================
import os

from six.moves.configparser import ConfigParser
from traits.api import (
    Str,
    Property,
    cached_property,
    Int,
    Any,
    String,
    Event,
    Bool,
    Dict,
    List,
    Button,
    CInt,
)

# ============= local library imports  ==========================
from pychron.core.helpers.filetools import glob_list_directory
from pychron.core.pychron_traits import LoadNameStr
from pychron.dvc.dvc_irradiationable import DVCAble
from pychron.entry.entry_views.user_entry import UserEntry
from pychron.globals import globalv
from pychron.paths import paths
from pychron.persistence_loggable import PersistenceLoggable
from pychron.pychron_constants import NULL_STR, LINE_STR, EXTRACT_DEVICE, FUSIONS


class ExperimentQueueFactory(DVCAble, PersistenceLoggable):
    application = Any

    username = String
    email = Property(depends_on="username, use_email, _email")
    _email = Str
    _emails = Dict

    use_group_email = Bool
    use_email = Bool
    edit_emails = Button

    usernames = Property(depends_on="users_dirty, db_refresh_needed")
    edit_user = Event
    add_user = Event
    users_dirty = Event
    db_refresh_needed = Event

    # mass_spectrometer = String("Spectrometer")
    # mass_spectrometers = Property(depends_on="db_refresh_needed")

    extract_device = String("Extract Device")
    extract_devices = Property(depends_on="db_refresh_needed")

    queue_conditionals_name = Str
    available_conditionals = List

    delay_between_analyses = Int(30)
    delay_before_analyses = Int(5)
    delay_after_blank = Int(15)
    delay_after_air = Int(15)
    delay_after_conditional = Str
    tray = Str
    trays = Property
    note = Str
    default_lighting = CInt(0)

    load_name = LoadNameStr(enter_set=True, auto_set=False)

    select_existing_load_name_button = Button

    # ok_make = Property(depends_on="mass_spectrometer, username")
    ok_make = Property(depends_on="username")

    persistence_name = "queue_factory"
    pattributes = (
        # "mass_spectrometer",
        "extract_device",
        "use_group_email",
        "delay_between_analyses",
        "delay_before_analyses",
        "delay_after_blank",
        "delay_after_air",
        "delay_after_conditional",
        "default_lighting",
        "queue_conditionals_name",
    )

    def activate(self, load_persistence):
        """
        called by ExperimentFactory
        """
        self._load_queue_conditionals()
        if load_persistence:
            self.load()
            self.username = globalv.username

    def deactivate(self):
        """
        called by ExperimentFactory.destroy
        """
        self.dump()

    # persistence
    def _load_queue_conditionals(self):
        root = paths.queue_conditionals_dir
        cs = glob_list_directory(root, remove_extension=True)
        self.available_conditionals = [NULL_STR] + cs

    # ===============================================================================
    # property get/set
    # ===============================================================================
    def _get_email(self):
        email = ""
        if self.use_email:
            if self._email:
                email = self._email
            else:
                if self.username in self._emails:
                    email = self._emails[self.username]
        return email

    def _set_email(self, v):
        self._email = v

    @cached_property
    def _get_ok_make(self):
        # ms = self.mass_spectrometer.strip()
        # return bool(ms and ms not in ("Spectrometer", LINE_STR) and un)
        un = self.username.strip()
        return bool(un)

    @cached_property
    def _get_trays(self):
        db = self.get_database()
        if db is None or not db.connect():
            return []

        trays = [NULL_STR]
        dbtrays = db.get_load_holders()
        if dbtrays:
            trays.extend(dbtrays)
        return trays

    @cached_property
    def _get_usernames(self):
        db = self.get_database()
        if db is None or not db.connect():
            return []

        us = []
        with db.session_ctx(use_parent_session=False):
            dbus = db.get_users()
            if dbus:
                us = [ui.name for ui in dbus]
                self._emails = {ui.name: ui.email or "" for ui in dbus}

        return [""] + us

    @cached_property
    def _get_extract_devices(self):
        """
        look in db first
        then look for a config file
        then use hardcorded defaults
        """
        db = self.get_database()
        cp = os.path.join(paths.setup_dir, "names")
        if db:
            if not db.connect():
                return []
            with db.session_ctx(use_parent_session=False):
                names = db.get_extraction_device_names()

        elif os.path.isfile(cp):
            names = self._get_names_from_config(cp, "Extraction Devices")
        else:
            names = FUSIONS
        return [EXTRACT_DEVICE, LINE_STR] + names

    # @cached_property
    # def _get_mass_spectrometers(self):
    #     """
    #     look in db first
    #     then look for a config file
    #     then use hardcorded defaults
    #     """
    #     db = self.get_database()
    #     cp = os.path.join(paths.setup_dir, "names")
    #     if db:
    #         if not db.connect():
    #             self.warning("not connected to database")
    #             return []
    #         with db.session_ctx(use_parent_session=False):
    #             ms = db.get_mass_spectrometer_names()
    #             names = [mi.capitalize() for mi in ms]
    #     elif os.path.isfile(cp):
    #         names = self._get_names_from_config(cp, "Mass Spectrometers")
    #     else:
    #         names = ["Jan", "Obama"]
    #
    #     return ["Spectrometer", LINE_STR] + names

    def _get_names_from_config(self, cp, section):
        config = ConfigParser()
        config.read(cp)
        if config.has_section(section):
            return [config.get(section, option) for option in config.options(section)]

    # handlers
    def _select_existing_load_name_button_fired(self):
        db = self.get_database()
        if db is None or not db.connect():
            self.warning_dialog("Not connected to a database")

        else:
            with db.session_ctx(use_parent_session=False):
                loads = db.get_loads()

                from pychron.database.views.load_view import LoadView

                lv = LoadView(records=loads)
                info = lv.edit_traits()
                if info.result:
                    self.load_name = lv.selected.name
                    self.tray = lv.selected.holderName

    def _edit_user_fired(self):
        a = UserEntry(dvc=self.dvc)

        nuser = a.edit(self.username)
        if nuser:
            self.users_dirty = True
            self.username = nuser

    # def _mass_spectrometer_changed(self, new):
    #     self.debug('mass spectrometer ="{}"'.format(new))

    def _edit_emails_fired(self):
        task = self.application.open_task("pychron.users")
        task.auto_save = True


if __name__ == "__main__":
    g = ExperimentQueueFactory()
    g.configure_traits()
# ============= EOF =============================================
