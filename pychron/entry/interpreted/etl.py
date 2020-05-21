# ===============================================================================
# Copyright 2020 ross
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
from pychron.dvc.dvc import DVCMixin
from pychron.dvc.dvc_orm import InterpretedParameterTbl, InterpretedTbl
from pychron.loggable import Loggable
from pychron.paths import paths

COLUMNS = ('sample', 'project', 'pi', 'material',
           'identifier', 'geologic_unit',
           'age', 'age_error',
           'kca', 'kca_error')


class InterpretedETL(Loggable, DVCMixin):
    def etl(self):
        """

        required columns
        sample, project, pi, material, identifier, geologic_unit, age, age_1sigma, kca, kca_1sigma

        get input file from user
        for each row in file
            extract
            transform
            load into dvc db
        :return:
        """
        self.dvc.create_session()
        delimiter = ','
        path = self.open_file_dialog(default_directory=paths.data_dir)

        # path = '/Users/ross/Sandbox/ds.csv'

        def tolist(line, lower=False):
            rs = [i.strip() for i in line.split(delimiter)]
            if lower:
                rs = [ri.lower() for ri in rs]
            return rs

        with open(path, 'r') as rf:
            header = tolist(next(rf), lower=True)
            missing_columns = [c for c in COLUMNS if c not in header]
            if missing_columns:
                self.warning_dialog('Invalid input file. Missing columns={}'.format(missing_columns))
                return

            for line in rf:
                iobj = self._extract(header, tolist(line))
                if self._validate(iobj):
                    self._transform(iobj)
                    self._load(iobj)

    def _validate(self, obj):
        return all((attr in obj for attr in COLUMNS))

    def _extract(self, header, line):
        return dict(zip(header, line))

    def _transform(self, iobj):
        pass

    def _load(self, iobj):
        dvc = self.dvc
        with dvc.session_ctx() as sess:
            i = InterpretedTbl()
            if not dvc.get_material(iobj['material']):
                return

            i.sample = dvc.add_sample(iobj['sample'],
                                      iobj.get('project', 'NoProject'),
                                      iobj('pi', 'NoPi'),
                                      iobj['material'])
            self.dvc.db.add_item(i)

            for attr, u in (('age', 'mA'), ('kca', 'dimensionless')):
                ip = InterpretedParameterTbl()
                ip.parameter = dvc.add_parameter(attr)
                ip.units = dvc.add_units(u)

                ip.value = iobj[attr]
                ip.error = iobj['{}_1sigma'.format(attr)]
                ip.interpreted = i
                self.dvc.db.add_item(ip)

            for attr in ('identifier', 'geologic_unit'):
                ip = InterpretedParameterTbl()
                ip.parameter = dvc.add_parameter(attr)
                ip.units = dvc.add_units('text')
                ip.text = iobj[attr]
                ip.interpreted = i
                self.dvc.db.add_item(ip)

# ============= EOF =============================================
