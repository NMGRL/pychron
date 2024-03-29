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
from __future__ import absolute_import

from datetime import datetime

from traits.api import HasTraits, List, Str, Float, Date, Any, TraitError

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.iterfuncs import groupby_key
from pychron.dvc.dvc_irradiationable import DVCAble
from pychron.paths import paths
from pychron.pychron_constants import DATE_FORMAT


class SensitivityRecord(HasTraits):
    user = Str(dictable=True)
    note = Str(dictable=True)
    mass_spectrometer = Str(dictable=True)
    sensitivity = Float(dictable=True)
    create_date = Date(dictable=True)
    units = Str("mol/fA", dictable=True)

    def to_dict(self):
        d = {k: getattr(self, k) for k in self.traits(dictable=True)}

        cd = d["create_date"]
        if not cd:
            self.create_date = cd = datetime.now()

        d["create_date"] = cd.strftime(DATE_FORMAT)
        return d

    @classmethod
    def from_dict(cls, d):
        record = cls()
        for attr in record.traits(dictable=True):
            if attr == "create_date":
                cd = d.get(attr)
                if cd and not isinstance(cd, datetime):
                    cd = datetime.strptime(cd, DATE_FORMAT)
                record.create_date = cd
            else:
                try:
                    setattr(record, attr, d.get(attr))
                except TraitError:
                    pass
        return record

    # primary_key = Int
    # editable = Bool(True)

    # def __init__(self, rec=None, *args, **kw):
    #     super(SensitivityRecord, self).__init__(*args, **kw)
    #     if rec:
    #         self._create(rec)
    #
    # def _create(self, dbrecord):
    #     self.user = dbrecord.user or ''
    #     self.note = dbrecord.note or ''
    #     self.create_date = dbrecord.create_date
    #     self.primary_key = int(dbrecord.id)
    #     self.editable = False
    #
    #     if dbrecord.mass_spectrometer:
    #         self.mass_spectrometer = dbrecord.mass_spectrometer.name
    #
    #     self.sensitivity = dbrecord.sensitivity
    #
    # def flush(self, dbrecord):
    #     attrs = ['sensitivity', 'note', 'user']
    #     for ai in attrs:
    #         v = getattr(self, ai)
    #         setattr(dbrecord, ai, v)


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

# class database_enabled(object):
#     def __call__(self, func):
#         def wrapper(obj, *args, **kw):
#             if obj.db is not None:
#                 return func(obj, *args, **kw)
#             else:
#                 obj.warning('database not enabled')
#
#         return wrapper


class SensitivityEntry(DVCAble):
    records = List(SensitivityRecord)
    selected = Any

    def _add_item(self, db):
        pass

    def activate(self):
        self._load_records()

    # @database_enabled()
    def _load_records(self):
        specs = self.dvc.get_sensitivities()
        print("asdf", specs)
        self.records = [
            SensitivityRecord.from_dict(sens)
            for spec in specs.values()
            for sens in spec
        ]

    # @database_enabled()
    def save(self):
        sens = {}
        for ms, ss in groupby_key(self.records, "mass_spectrometer"):
            sens[ms] = [ri.to_dict() for ri in ss]

        self.dvc.save_sensitivities(sens)

    def add(self):
        rec = SensitivityRecord()
        self.records.append(rec)


# ===============================================================================
# handlers
# ===============================================================================
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
# ===============================================================================
# property get/set
# ===============================================================================
#     def _get_records(self):
#         if not self._records:
#             recs = self.db.get_sensitivities()
#             self._records = [SensitivityRecord(dbrecord=ri) for ri in recs]
#         return self._records

# ===============================================================================
# views
# ===============================================================================
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


if __name__ == "__main__":
    from pychron.core.helpers.logger_setup import logging_setup

    paths.build("_experiment")

    logging_setup("runid")
    m = SensitivityEntry()
    m.configure_traits()
# ============= EOF =============================================
