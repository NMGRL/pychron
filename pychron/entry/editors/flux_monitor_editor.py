# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from sqlalchemy.exc import DBAPIError
from traits.api import HasTraits, Float, Str, List, Instance, Property, Button, Bool, Event
from traitsui.api import View, Item, HGroup, VGroup, UItem, ListStrEditor, VSplit

from pychron.database.isotope_database_manager import IsotopeDatabaseManager
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.pychron_constants import PLUSMINUS_ONE_SIGMA


# ============= standard library imports ========================
# ============= local library imports  ==========================


class FluxMonitor(HasTraits):
    name = Str
    age = Float
    age_err = Float
    decay_constant = Float
    decay_constant_err = Float
    ref=Str
    added=Bool(False)

    def to_dict(self):
        return dict(age=self.age, age_err=self.age_err,
                    decay_constant=self.decay_constant,
                    decay_constant_err=self.decay_constant_err)

    def traits_view(self):
        v = View(VGroup(
            HGroup(Item('name',enabled_when='added')),
            HGroup(Item('age'), Item('age_err', label=PLUSMINUS_ONE_SIGMA)),
            HGroup(Item('decay_constant'), Item('decay_constant_err', label=PLUSMINUS_ONE_SIGMA)),
            ))
        return v


class FluxMonitorEditor(IsotopeDatabaseManager):

    # dbname = Str
    # names = List
    monitors=List
    monitor_names=Property(depends_on='name_update_needed,monitors[]')
    selected_monitor_name=Str

    selected_monitor=Instance(FluxMonitor, ())

    add_button=Button
    delete_button=Button
    name_update_needed=Event
    activated=Event
    def _get_monitor_names(self):
        return [mi.name for mi in self.monitors]

    def add_flux_monitor(self):
        self._load_monitors()
        info=self.edit_traits()
        if info.result:
            self._save()

    def _save(self):
        #save any added flux monitors

        db = self.db
        with db.session_ctx():
            for m in self.monitors:
                if m.added:
                    if db.get_flux_monitor(m.name, key='name'):
                        self.warning('"{}" already exists in database'.format(m.name))
                    else:
                        db.add_flux_monitor(m.name, **m.to_dict())

            if self.selected_monitor:
                dbmon=db.get_flux_monitor(self.selected_monitor.name)
                if dbmon:
                    for k,v in self.selected_monitor.to_dict().iteritems():
                        setattr(dbmon,k,v)

        self.information_dialog('Changes saved to database')

    def _load_monitors(self):
        self.monitors=[]
        db=self.db
        with db.session_ctx():
            mons=db.get_flux_monitors()
            self.monitors=[self._flux_monitor_factory(mi) for mi in mons]

    def _flux_monitor_factory(self, mi):
        fm=FluxMonitor(age=mi.age or 0,
                       age_err=mi.age_err or 0, name=mi.name)
        return fm

    def _selected_monitor_name_changed(self, new):

        if new:
            m=next((mi for mi in self.monitors if mi.name==new))
            self.trait_set(selected_monitor=m)
            # self.selected_monitor=

    def _add_button_fired(self):

        fm=FluxMonitor(added=True, name='Untitled')
        self.monitors.append(fm)

        fm.on_trait_change(self._handle_name_change, 'name')

        self.selected_monitor=fm
        self.selected_monitor_name=fm.name

    #     name=self.selected_monitor.name
    #     db=self.db
    #     with db.session_ctx():
    #         if db.get_flux_monitor(name):
    def _handle_name_change(self):
        self.name_update_needed=True

    def _delete_button_fired(self):
        name=self.selected_monitor_name
        if self.confirmation_dialog('Are you sure you want to delete "{}"'.format(name)):

            db=self.db
            with db.session_ctx() as sess:
                dbmon=db.get_flux_monitor(name, key='name')
                sess.delete(dbmon)
                try:
                    sess.commit()
                    self.monitors.remove(self.selected_monitor)
                except DBAPIError, e:
                    self.warning('Error when trying to delete "{}".\n\n{}'.format(name, e))

    def traits_view(self):
        v = View(VSplit(
            VGroup(HGroup(icon_button_editor('add_button','database_add',
                                             tooltip='Add flux monitor to database'),
                          icon_button_editor('delete_button','database_delete',
                                             enabled_when='selected_monitor_name',
                                             tooltip='Delete selected flux monitor')),
            UItem('monitor_names', editor=ListStrEditor(selected='selected_monitor_name',
                                                        editable=False))),
                 UItem('selected_monitor',style='custom')),
                 buttons=['OK', 'Cancel'],
                 kind='livemodal',
                 title='Edit Flux Monitor')
        return v

        # ============= EOF =============================================
