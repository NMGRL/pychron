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
#===============================================================================

#============= enthought library imports =======================
from traits.api import Str, Property, cached_property, Int, \
    Any, String, Event, Bool, Dict, List
#============= standard library imports ========================
import os
from ConfigParser import ConfigParser
#============= local library imports  ==========================
from pychron.core.helpers.filetools import list_directory2
from pychron.entry.user_entry import UserEntry
from pychron.experiment.utilities.persistence_loggable import PersistenceLoggable
from pychron.pychron_constants import NULL_STR, LINE_STR
from pychron.paths import paths


class ExperimentQueueFactory(PersistenceLoggable):
    db = Any
    application = Any

    username = String
    email = Property(depends_on='username, use_email_notifier, _email')
    _email = Str
    _emails = Dict

    use_email_notifier = Bool(True)

    usernames = Property(depends_on='users_dirty')
    edit_user = Event
    add_user = Event
    users_dirty = Event

    mass_spectrometer = String('Spectrometer')
    mass_spectrometers = Property

    extract_device = String('Extract Device')
    extract_devices = Property

    use_queue_conditionals = Bool
    queue_conditionals_name = Str
    available_conditionals = List

    delay_between_analyses = Int(30)
    delay_before_analyses = Int(5)
    tray = Str
    trays = Property

    load_name = Str
    load_names = Property

    ok_make = Property(depends_on='mass_spectrometer, username')

    pattributes = ('username', 'mass_spectrometer', 'extract_device',
                   'delay_between_analyses',
                   'delay_before_analyses', 'use_queue_conditionals',
                   'queue_conditionals_name')
    # def _add_user_fired(self):
    #     a=UserEntry()
    #     a.edit_user(self.username)
    #     self.users_dirty=True
    def activate(self, load_persistence):
        """
            called by ExperimentFactory
        """
        self._load_queue_conditionals()
        if load_persistence:
            self.load()

    def deactivate(self):
        """
            called by ExperimentFactory.destroy
        """
        self.dump()

    def _load_queue_conditionals(self):
        root = paths.queue_conditionals_dir
        cs = list_directory2(root, remove_extension=True)
        self.available_conditionals = cs

    def _edit_user_fired(self):
        a = UserEntry()
        nuser = a.add_user(self.username)
        if nuser:
            self.users_dirty = True
            self.username = nuser

    #persistence
    @property
    def persistence_path(self):
        return os.path.join(paths.hidden_dir, 'queue_factory')

    #===============================================================================
    # property get/set
    #===============================================================================
    def _get_email(self):
        email = ''
        if self.use_email_notifier:
            if self._email:
                email = self._email
            else:
                if self.username in self._emails:
                    email = self._emails[self.username]
        return email

    def _set_email(self, v):
        self._email = v

    @cached_property
    def _get_usernames(self):
        db = self.db
        with db.session_ctx():
            dbus = db.get_users()
            us = [ui.name for ui in dbus]
            self._emails = dict([(ui.name, ui.email or '') for ui in dbus])

            return [''] + us

    @cached_property
    def _get_load_names(self):
        with self.db.session_ctx():
            ts = self.db.get_loads()
            names = [ti.name for ti in ts]
            return names

    def _get_ok_make(self):
        ms = self.mass_spectrometer.strip()
        un = self.username.strip()
        #        ed = self.extract_device.strip()

        return ms and not ms in ('Spectrometer', LINE_STR) and un

    #                ed and ed != NULL_STR and  \
    #                    un

    @cached_property
    def _get_trays(self):
        return [NULL_STR]

    @cached_property
    def _get_extract_devices(self):
        """
            look in db first
            then look for a config file
            then use hardcorded defaults
        """
        cp = os.path.join(paths.setup_dir, 'names')
        if self.db:
            eds = self.db.get_extraction_devices()
            names = [ei.name for ei in eds]
        elif os.path.isfile(cp):
            names = self._get_names_from_config(cp, 'Extraction Devices')
        else:
            names = ['Fusions Diode', 'Fusions UV', 'Fusions CO2']
        return ['Extract Device', LINE_STR] + names

    @cached_property
    def _get_mass_spectrometers(self):
        """
            look in db first
            then look for a config file
            then use hardcorded defaults
        """
        cp = os.path.join(paths.setup_dir, 'names')
        if self.db:
            ms = self.db.get_mass_spectrometers()
            names = [mi.name.capitalize() for mi in ms]
        elif os.path.isfile(cp):
            names = self._get_names_from_config(cp, 'Mass Spectrometers')
        else:
            names = ['Jan', 'Obama']

        return ['Spectrometer', LINE_STR] + names

    def _get_names_from_config(self, cp, section):
        config = ConfigParser()
        config.read(cp)
        if config.has_section(section):
            return [config.get(section, option) for option in config.options(section)]

    def _mass_spectrometer_changed(self, new):
        self.debug('mass spectrometer ="{}"'.format(new))


if __name__ == '__main__':
    g = ExperimentQueueFactory()
    g.configure_traits()
#============= EOF =============================================
