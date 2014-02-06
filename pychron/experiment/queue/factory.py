#===============================================================================
# Copyright 2012 Jake Ross
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
from ConfigParser import ConfigParser

from traits.api import Str, Property, cached_property, Int, \
    Any, String, Event

from pychron.entry.user_entry import UserEntry
from pychron.loggable import Loggable
from pychron.pychron_constants import NULL_STR, LINE_STR
from pychron.paths import paths




#============= standard library imports ========================
#============= local library imports  ==========================

class ExperimentQueueFactory(Loggable):
    db = Any
    application = Any

    username = Str
    usernames = Property(depends_on='users_dirty')
    edit_user = Event
    add_user = Event
    users_dirty = Event

    mass_spectrometer = String('Spectrometer')
    mass_spectrometers = Property

    extract_device = String('Extract Device')
    extract_devices = Property

    delay_between_analyses = Int(30)
    delay_before_analyses = Int(5)
    tray = Str
    trays = Property

    load_name = Str
    load_names = Property

    ok_make = Property(depends_on='mass_spectrometer, username')

    # def _add_user_fired(self):
    #     a=UserEntry()
    #     a.edit_user(self.username)
    #     self.users_dirty=True

    def _edit_user_fired(self):
        a = UserEntry()
        nuser = a.add_user(self.username)
        if nuser:
            self.users_dirty = True
            self.username = nuser

    #===============================================================================
    # property get/set
    #===============================================================================
    @cached_property
    def _get_usernames(self):
        db = self.db
        with db.session_ctx():
            us = [ui.name for ui in db.get_users()]
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


if __name__ == '__main__':
    g = ExperimentQueueFactory()
    g.configure_traits()
#============= EOF =============================================
