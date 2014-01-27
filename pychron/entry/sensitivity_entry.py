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
from traits.api import HasTraits, List, Str, Int, Float, \
    Date, Any, Bool
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.paths import paths
from pychron.database.isotope_database_manager import IsotopeDatabaseManager


class SensitivityRecord(HasTraits):
    user = Str
    note = Str
    mass_spectrometer = Str
    sensitivity = Float
    create_date = Date
    primary_key = Int
    editable = Bool(True)

    def __init__(self, rec=None, *args, **kw):
        super(SensitivityRecord, self).__init__(*args, **kw)
        if rec:
            self._create(rec)

    def _create(self, dbrecord):
        self.user = dbrecord.user or ''
        self.note = dbrecord.note or ''
        self.create_date = dbrecord.create_date
        self.primary_key = int(dbrecord.id)
        self.editable = False

        if dbrecord.mass_spectrometer:
            self.mass_spectrometer = dbrecord.mass_spectrometer.name

        self.sensitivity = dbrecord.sensitivity

    def flush(self, dbrecord):
        attrs = ['sensitivity', 'note', 'user']
        for ai in attrs:
            v = getattr(self, ai)
            setattr(dbrecord, ai, v)


#     dbrecord = Any
#     spectrometer = Property
#     _spectrometer = Str
#
#     def _get_spectrometer(self):
#
#         if self._spectrometer:
#             return self._spectrometer
#
#         if self.dbrecord:
#             return self.dbrecord.mass_spectrometer.name
#
#     def _set_spectrometer(self, v):
#         self._spectrometer = v
#
#     def __getattr__(self, attr):
#         if hasattr(self.dbrecord, attr):
#             return getattr(self.dbrecord, attr)

#     def sync(self, spec):
#         attrs = ['sensitivity', 'note', 'user']
#         for ai in attrs:
#             v = getattr(self, ai)
#             setattr(self.dbrecord, ai, v)
#
#         self.dbrecord.mass_spectrometer = spec


class SensitivityEntry(IsotopeDatabaseManager):
    records = List(SensitivityRecord)
    #     records = Property(List(SensitivityRecord),
    #                        depends_on='_records'
    #                        )
    #     _records = List
    #     add_button = Button('+')
    #     save_button = Button('save')
    selected = Any

    def activate(self):
        self.load_records()

    def load_records(self):
        db = self.db
        with db.session_ctx():
            recs = self.db.get_sensitivities()
            self.records = [SensitivityRecord(ri)
                            for ri in recs]

    def save(self):
        db = self.db
        with db.session_ctx():
            for si in self.records:
                dbrecord = db.get_sensitivity(si.primary_key)
                if dbrecord is None:
                    dbrecord = db.add_sensitivity()

                si.flush(dbrecord)

    def add(self):
        rec = SensitivityRecord()
        self.records.append(rec)

    def paste(self, obj):
        return obj.clone_traits(traits=['mass_spectrometer',
                                        'sensitivity'])

#===============================================================================
# handlers
#===============================================================================
#     def _add_button_fired(self):
#         s = SensitivityRecord()
#         self._records.append(s)
# #        self.records_dirty = True
#     def _save_button_fired(self):
#         db = self.db
#         for si in self.records:
# #            print si.note, si.dbrecord.
#             if si.dbrecord is None:
#                 user = si.user
#                 if user == 'None':
#                     user = db.save_username
#                 db.add_sensitivity(si.spectrometer,
#                                    user=user, note=si.note, sensitivity=si.sensitivity)
#             else:
#                 spec = db.get_mass_spectrometer(si.spectrometer)
#                 si.sync(spec)
# #                for ai in ['sensitivity','']
#
#
#
#         db.commit()
#===============================================================================
# property get/set
#===============================================================================
#     def _get_records(self):
#         if not self._records:
#             recs = self.db.get_sensitivities()
#             self._records = [SensitivityRecord(dbrecord=ri) for ri in recs]
#         return self._records

#===============================================================================
# views
#===============================================================================
#     def traits_view(self):
#         v = View(Item('records', show_label=False,
#                       editor=TabularEditor(adapter=SensitivityAdapter(),
#                                            operations=['edit'],
#                                            editable=True,
#                                            )
#                       ),
#
#                  HGroup(Item('add_button', show_label=False),
#                         Item('save_button', show_label=False)),
#                  resizable=True,
#                  width=500,
#                  height=200,
#                  title='Sensitivity Table'
#                  )
#         return v

class SensitivitySelector(SensitivityEntry):
    pass


if __name__ == '__main__':
    from pychron.core.helpers.logger_setup import logging_setup

    paths.build('_experiment')

    logging_setup('runid')
    m = SensitivityEntry()
    m.configure_traits()
#============= EOF =============================================
