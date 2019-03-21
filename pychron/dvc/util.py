# ===============================================================================
# Copyright 2019 ross
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


# ============= EOF =============================================
from uncertainties import ufloat

from pychron.dvc import analysis_path, dvc_dump
from pychron.processing.interpreted_age import InterpretedAge


class Tag(object):
    name = None
    path = None
    note = ''
    subgroup = ''
    uuid = ''
    record_id = ''

    @classmethod
    def from_analysis(cls, an, **kw):
        tag = cls()
        tag.name = an.tag
        tag.note = an.tag_note
        tag.record_id = an.record_id
        tag.uuid = an.uuid
        tag.repository_identifier = an.repository_identifier
        # tag.path = analysis_path(an.record_id, an.repository_identifier, modifier='tags')
        tag.path = analysis_path(an, an.repository_identifier, modifier='tags')
        tag.subgroup = an.subgroup

        for k, v in kw.items():
            setattr(tag, k, v)

        return tag

    def dump(self):
        obj = {'name': self.name,
               'note': self.note,
               'subgroup': self.subgroup}
        if not self.path:
            self.path = analysis_path(self.uuid, self.repository_identifier, modifier='tags', mode='w')

        dvc_dump(obj, self.path)


class DVCInterpretedAge(InterpretedAge):
    labnumber = None
    isotopes = None
    repository_identifier = None
    analyses = None

    def load_tag(self, obj):
        self.tag = obj.get('name', '')
        self.tag_note = obj.get('note', '')

    def from_json(self, obj):
        for attr in ('name', 'uuid'):
            setattr(self, attr, obj.get(attr, ''))

        pf = obj['preferred']
        for attr in ('age', 'age_err'):
            setattr(self, attr, pf.get(attr, 0))

        sm = obj['sample_metadata']
        for attr in ('sample', 'material', 'project', 'irradiation'):
            setattr(self, attr, sm.get(attr, ''))

        # for a in ('age', 'age_err', 'age_kind',
        #           # 'kca', 'kca_err','kca_kind',
        #           'mswd',
        #           'sample', 'material', 'identifier', 'nanalyses', 'irradiation',
        #           'name', 'project', 'uuid', 'age_error_kind'):
        #     try:
        #         setattr(self, a, obj.get(a, NULL_STR))
        #     except BaseException as a:
        #         print('exception DVCInterpretdAge.from_json', a)

        self.labnumber = self.identifier
        # self.uage = ufloat(self.age, self.age_err)
        self._record_id = '{} {}'.format(self.identifier, self.name)

        self.analyses = obj.get('analyses', [])

        pkinds = pf.get('preferred_kinds')
        if pkinds:
            for k in pkinds:
                attr = k['attr']
                if attr == 'age':
                    attr = 'uage'
                setattr(self, attr, ufloat(k['value'], k['error']))

    def get_value(self, attr):
        try:
            return getattr(self, attr)
        except AttributeError:
            return ufloat(0, 0)

    @property
    def status(self):
        return 'X' if self.is_omitted() else ''