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
import os

from pychron.experiment.classifier.isotope_classifier import IsotopeClassifier
from pychron.paths import paths

paths.build('_dev')

# ============= enthought library imports =======================
from traits.api import Instance, Button
from traitsui.api import View, UItem, HGroup, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.handler import Handler
from pychron.dvc.dvc import DVC
from pychron.graph.stacked_regression_graph import StackedRegressionGraph
from pychron.loggable import Loggable

UUIDS = (
    'f051a564-d471-4dc7-b143-de6deb97befb',
    '880e2fbe-9f44-41f3-890a-18e4b54a9f4d',
    '130b6320-2e70-4a22-a96f-4a481de66728',
    '9434648f-4edc-4ec7-a978-fda4a9f4bcb5',
    'fe1208a9-4147-44dc-8610-56dfe1fc55f7',
    'b4ea67bf-d9c8-42b7-a9fc-bc5c1ff4cd1b',
    'e1fa4315-eab7-46a9-995d-ab461f99b5f9',
    '586f25ef-5895-4b50-b9fd-777dc84aed5e',
    '64c7364a-6c91-45c8-a1a1-80ab62876d24',
    'c4b05455-5698-4d1f-892a-a665c3dfe1f3',
    'd53c4f73-0faa-4953-93fb-fda85f4aad50',
    '0f0e4f50-0bb3-40df-838e-26f2c08adb25',
    'b8ca05bf-dad2-4136-9254-4d90d50e6256',
    '9bf62150-977a-4684-a930-0629cccb3fed',
    '3e285a9c-0f5f-4d7b-86f7-432316c8fd75',
    'f4e6d50d-56b1-402a-9d54-2146926a46c7',
    '30a1a5ae-874f-45c9-809c-6341b11483cb',
    '85634a4c-1287-4fbb-858b-804f461f6bb5',
    '63ac8fb1-d162-4a74-b749-fac58eccb29b',
    '1a0c758d-53f7-476a-a023-44e1b27f1db5',
    'e5f2703f-ef05-47cf-a362-e3832c77fc4f',
    '2983bd3b-4ffd-4104-952c-d3ecb0c6ba03',
    '72c1bed7-7548-4bfe-bb2e-1beba8cdbfb3',
    '916afcd0-3999-43e9-ac13-518f5ba42cb1',
    '58ae6734-48fd-46e4-a31c-38e8b1a17465',
    'a08a3d4a-eb40-47ee-bdda-793931190893',
    '2ad3d6ab-b224-43b3-83c3-409069d1190c',
    '32c6b38d-c556-44a9-8ce0-1cbc2450aa7a',
    'efd1d1ea-cc07-4ec6-907a-5d6633b7c867',
    'd4992230-b5be-43c5-8944-24fc57746617',
    '8f64f400-b876-4607-9df2-6121338fd991',
    'b1628c47-fc71-4547-be26-2c0b08ff1605',
    'cf0fd0cb-6164-492c-b56d-069bc3b5e0e2',
    '1101d357-3d87-4773-8e51-0278eb9d196d',
    'dcc0ae08-9427-47fd-9d69-3d6b6d553107',
    '048e59cc-cc10-4e32-85cd-175ab53ebc78',
    '2857c9f8-1785-4a42-b451-9782057b8d94',
    '26e7df9f-b3ba-4f63-ac7e-a3b309b0476f',
    'f3f957f1-2bb6-453d-a5a9-12ec490ab804',
    '927a0a80-e855-4166-81e4-75ef82b652e1',
    '74c27aa3-71bc-4789-a925-77de3cb0c6f7',
    '1e5cb143-b618-4468-ac6d-a1b34abc7736',
    '6e72cf2b-4767-4530-83ea-795d6c6a8024',
    'cac02d85-0d78-4ec5-a0f7-40859cc65147',
    '936a03e8-8967-4da3-9b79-672cfdc07c9b',
    'ab2e3743-3ced-4f22-b98f-34b4f8889d7e',
    'c2ba0b16-a014-40a8-9ca4-0c5195d66f91',
    '6bfab236-a6c6-4ad5-af88-b236d9c94452',
    '7b8b9538-1326-46d8-863e-cbb65e1b6ded',
    '1ccb8070-8de4-460c-8616-e64a41460d67',
    '55ff6bf7-e3c1-413b-982f-65e4626cc09d',
    '7714ba5a-0d57-421e-a00a-658d49dc1300',
    '0c963d9b-46dc-4604-ad28-c5ba212c54fb',
    '260c4041-de1f-428e-90f3-217ba9ee61e7',
    '36bb2001-a553-42e4-a07a-185d4c8552f1',
    '097e62e8-f3bd-4ed9-8cd8-c59dcdec2518',
    '5c2bfc08-db29-4cef-9c67-ebdfcfbc3055',
    'e27501b5-ecaf-4e7b-b31a-6bc2a7e2b6e7',
    '9b90a9e5-c1ec-4652-a28e-d6e3df5c2182',
    'a267fbe0-572c-48fd-9c0f-b32dec1dad3b',
    'f2d8127d-e0aa-4c10-97f4-9973ce62a009',
    '45ea82a2-c583-40a1-a105-5c881180593c',
    '1a524aa0-1485-470f-9e0c-a2b61a6810f3',
    'd3176129-a8f3-4888-87bd-7d2ec94ab30f',
    '04b2c685-893a-466c-bb44-44e316cd9b65',
    '73a0b227-2f3a-4757-bffa-c63affd4a16c',
    '8b7a732c-47ee-4ff7-ac44-cd15d748352d',
    '3c0566af-66d2-4aba-a562-745b4838173a',
    'e0790f8d-820d-4212-a2ef-aa2f806556fc',
    '55b029b7-6bad-46ce-962d-3dfbbdc128fa',
    '24861f61-2661-4b93-82a7-f69d61850931',
    'eb8f77c5-aa68-45df-9627-4d6a8383b999',
    'c8a60108-b43d-4b7e-8748-665549da2bed',
    'c1accc71-8f4e-4705-837a-90c8589ddad0',
    'cbe593ee-ea4c-4cc5-a72f-f2ef0cf05e92',
    '92122f35-635f-4b29-95df-674f39b443c4',
    '27fcf9b5-7d08-45c7-a1bb-b9befe8b0807',
    'd75b4eec-d68f-4f49-8bad-e798fe5d3882',
    '57f1a6bc-ab09-4473-827c-718dca96a94d',
    '9725492e-34f1-41fb-aaee-90a45b779773',
    'ee3f9e1a-c589-49ff-8415-9ce42d48336e',
    '794562b4-2f6d-45a2-82dc-76b1a743db31',
    '8fa4e458-d09c-4f0c-b038-6de6a74eeff8',
    '0e454e12-db8b-4e84-8102-eda92e6ff0f3',
    '39805525-a9af-45bd-b59e-f220faddddc2',
    '5eebb98b-25f6-424b-ae05-f0d34777ba32',
    'c9f37fa7-9989-4541-9128-8ab35f5fcd3a',
    'bd9903e7-d361-4407-af78-df577a079171',
    '3911148e-7771-41da-a4c9-8d6cb6b90805',
    '185a9b7d-4658-4177-bfb0-8e250101dce0',
    '0a06519c-8956-43db-8b8a-0e63b38ac03e',
    'aa643c29-bcb1-4b87-ac5c-2f168a0d8740',
    '66ad54e1-2689-49da-8ace-80dc26f079d5',
    '0c424c7e-8559-4597-b649-809a23cb4286',
    '997c7c24-dedb-46c6-8831-05ffbacbc782',
    'd7378321-64c6-4338-b9e4-affb2c8d43ff',
    '931a58e5-865b-4049-8679-bfcea78cc18f',
    'e99a4a31-4d83-49d5-b80d-413d075729f3',
    '0b7ae7dc-6c33-423e-9024-190544f6b792',
    '5126b4a8-8bb8-42eb-a605-252c7c4c9c4b',
)


class KlassHandler(Handler):
    def object_good_button_changed(self, info):
        info.object.klass = 1
        info.ui.dispose()

    def object_bad_button_changed(self, info):
        info.object.klass = 0
        info.ui.dispose()


class IsotopeTrainer(Loggable):
    graph = Instance(StackedRegressionGraph)
    good_button = Button
    bad_button = Button
    test = Button
    klass = None

    def setup_graph(self, iso):
        self.klass = None

        g = StackedRegressionGraph()
        g.new_plot(padding=[60, 10, 10, 40])
        if iso:
            g.new_series(iso.xs, iso.ys,
                         fit=iso.fit,
                         filter_outliers_dict=iso.filter_outliers_dict)
            g.set_x_limits(min_=0, max_=iso.xs[-1] * 1.1)
            g.set_y_title(iso.name)

        g.set_x_title('Time (s)')

        g.refresh()
        self.graph = g

    def train(self):
        dvc = DVC(bind=False,
                  organization='NMGRLData')
        dvc.db.trait_set(name='pychronmeta1',
                         username=os.environ.get('ARGONSERVER_DB_USER'),
                         password=os.environ.get('ARGONSERVER_DB_PWD'),
                         kind='mysql',
                         host=os.environ.get('ARGONSERVER_HOST'))
        dvc.connect()
        isos = []
        klasses = []
        uuids = UUIDS
        with dvc.session_ctx():
            for uuid in uuids:
                broke = False
                dbai = dvc.get_analysis_uuid(uuid)
                ai = dvc.make_analyses((dbai,))[0]
                ai.load_raw_data()
                for iso in ai.isotopes.values():

                    klass = self._get_klass(iso)
                    if klass is not None:
                        isos.append(iso)
                        klasses.append(klass)
                    else:
                        broke = True
                        break

                if broke:
                    break

        if isos:
            clf = IsotopeClassifier()
            clf.add_isotopes(isos, klasses)
            clf.dump()

    def _get_klass(self, iso):
        self.setup_graph(iso)
        bgrp = HGroup(UItem('good_button'), UItem('bad_button'))
        self.edit_traits(view=View(VGroup(bgrp, UItem('graph', style='custom')),
                                   buttons=['Cancel']),
                         kind='livemodal',
                         handler=KlassHandler())
        return self.klass

    def _test_fired(self):
        # self._get_klass(None)
        self.train()


if __name__ == '__main__':
    t = IsotopeTrainer()
    t.configure_traits(view=View('test'))

# ============= EOF =============================================
