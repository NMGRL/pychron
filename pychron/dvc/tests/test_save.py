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
from pychron.core.ui import set_qt
from pychron.processing.isotope import Isotope

set_qt()
# ============= enthought library imports =======================
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.experiment.automated_run.persistence_spec import PersistenceSpec
from pychron.experiment.automated_run.spec import AutomatedRunSpec
from pychron.processing.arar_age import ArArAge
from pychron.dvc.dvc import DVC
from pychron.dvc.dvc_persister import DVCPersister
from pychron.paths import paths


def test_save_persister():
    paths.build('_dev')
    dvc = DVC(bind=False)
    dvc.db.connect()

    per = DVCPersister(dvc=dvc)

    run_spec = AutomatedRunSpec()
    run_spec.labnumber = '10001'
    run_spec.project = 'Test'

    arar = ArArAge()
    arar.isotopes['Ar40'] = Isotope(xs=[1, 2, 3], ys=[1, 2, 3],
                                    name='Ar40', detector='H1')
    sd = {}
    dd = {'H1': 100}
    gd = {'H1': 1.021}
    per_spec = PersistenceSpec(run_spec=run_spec,
                               arar_age=arar,
                               spec_dict=sd,
                               defl_dict=dd,
                               gains=gd,
                               positions=[1, ],
                               experiment_queue_name='testexp.txt',
                               measurement_name='jan_unknown.py',
                               extraction_name='foo.py')

    per.per_spec_save(per_spec)
    # per.pre_extraction_save()
    # per.pre_measurement_save()
    # per.post_extraction_save('rblobbbasdf', 'oblobasdfas', None)
    # per.post_measurement_save()


if __name__ == '__main__':
    test_save_persister()
# ============= EOF =============================================
