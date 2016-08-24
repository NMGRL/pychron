# ===============================================================================
# Copyright 2013 Jake Ross
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
from envisage.ui.tasks.task_extension import TaskExtension
from envisage.ui.tasks.task_factory import TaskFactory
from pyface.tasks.action.schema import SMenu, SGroup
from pyface.tasks.action.schema_addition import SchemaAddition

from pychron.entry.editors.flux_monitor_editor import FluxMonitorEditor
from pychron.entry.editors.molecular_weight_editor import MolecularWeightEditor
from pychron.entry.tasks.actions import MakeIrradiationBookPDFAction, MakeIrradiationTemplateAction, \
    SensitivityEntryAction, AddMolecularWeightAction, AddFluxMonitorAction, \
    GenerateTrayAction, \
    ImportIrradiationHolderAction, ExportIrradiationAction, ImportIrradiationAction, \
    TransferJAction, ImportSamplesAction, ImportIrradiationFileAction, GetIGSNAction, GenerateIrradiationTableAction
from pychron.entry.tasks.labnumber.actions import LabnumberEntryAction
from pychron.entry.tasks.preferences import LabnumberEntryPreferencesPane, SamplePrepPreferencesPane
from pychron.entry.tasks.sample.actions import SampleEntryAction, SampleEditAction
from pychron.entry.tasks.sample_prep.actions import SamplePrepAction
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin


class EntryPlugin(BaseTaskPlugin):
    id = 'pychron.entry.plugin'

    def _help_tips_default(self):
        return ['Use <b>Entry>Labnumber</b> to add/edit irradiation information including '
                'Irradiation, Level, Sample, Project, Labnumber, etc...',

                'Use <b>Entry>Sensitivity</b> to add/edit the sensitivity table.',

                'Once the Labnumber window is activated additional Menu actions are available including, '
                'Transfer J and Generate Labbook.']

    def _actions_default(self):
        return [('pychron.labnumber_entry', 'Ctrl+Shift+l', 'Open Labnumber Entry Window'),
                ('pychron.sensitivity', 'Ctrl+Shift+\\', 'Open Sensistivity Window'), ]

    def _service_offers_default(self):
        def factory():
            dvc = self.application.get_service('pychron.dvc.dvc.DVC')
            e = MolecularWeightEditor(dvc=dvc)
            return e

        def factory2():
            dvc = self.application.get_service('pychron.dvc.dvc.DVC')
            e = FluxMonitorEditor(dvc=dvc)
            return e

        so1 = self.service_offer_factory(factory=factory,
                                         protocol=MolecularWeightEditor, )
        so2 = self.service_offer_factory(factory=factory2,
                                         protocol=FluxMonitorEditor)
        return [so1, so2]

    def _task_extensions_default(self):
        extensions = [TaskExtension(actions=actions, task_id=eid) for eid, actions in self._get_extensions()]
        additions = [SchemaAddition(id='entry', factory=lambda: SMenu(id='entry.menu', name='Entry'), path='MenuBar',
                                    before='tools.menu', after='view.menu')]

        eflag = False
        eeflag = False
        for eid, actions in self._get_extensions():
            # print 'b', eid, len(actions)
            for ai in actions:
                # print 'c',ai,ai.id
                if not eflag and ai.id.startswith('pychron.entry1'):
                    eflag = True
                    additions.append(SchemaAddition(id='entry_group', factory=lambda: SGroup(id='entry.group'),
                                                    path='MenuBar/entry.menu'))
                    additions.append(SchemaAddition(id='entry_sample_group',
                                                    absolute_position='first',
                                                    factory=lambda: SGroup(id='entry.sample.group'),
                                                    path='MenuBar/entry.menu'))
                elif not eeflag and ai.id.startswith('pychron.entry2'):
                    eeflag = True
                    additions.append(SchemaAddition(id='entry_group2', factory=lambda: SGroup(id='entry.group2'),
                                                    after='entry_group',
                                                    path='MenuBar/entry.menu'), )

        extensions.append(TaskExtension(actions=additions))

        return extensions

    def _available_task_extensions_default(self):
        g2path = 'MenuBar/entry.menu/entry.group2'
        gpath = 'MenuBar/entry.menu/entry.group'
        spath = 'MenuBar/entry.menu/entry.sample.group'

        return [('{}.entry2'.format(self.id),
                 'pychron.entry.irradiation.task',
                 'Entry Tools',
                 [SchemaAddition(id='pychron.entry2.transfer_j', factory=TransferJAction, path=g2path),
                  SchemaAddition(id='pychron.entry2.get_igsns', factory=GetIGSNAction, path=g2path),
                  SchemaAddition(id='pychron.entry2.import_irradiation', factory=ImportIrradiationAction, path=g2path),
                  SchemaAddition(id='pychron.entry2.export_irradiation', factory=ExportIrradiationAction, path=g2path),
                  SchemaAddition(id='pychron.entry2.import_samples_from_file', factory=ImportSamplesAction,
                                 path=g2path),
                  SchemaAddition(id='pychron.entry2.import_irradiations_from_file', factory=ImportIrradiationFileAction,
                                 path=g2path),
                  SchemaAddition(id='pychron.entry2.generate_tray', factory=GenerateTrayAction, path=g2path, ),
                  SchemaAddition(id='pychron.entry2.save_labbook', factory=MakeIrradiationBookPDFAction, path=g2path)]),
                (self.id, '', 'Entry',
                 [SchemaAddition(id='pychron.entry1.sample_entry', factory=SampleEntryAction,
                                 path=spath, absolute_position='first'),
                  SchemaAddition(id='pychron.entry1.sample_edit', factory=SampleEditAction,
                                 path=spath, after='pychron.entry1.sample_entry'),
                  SchemaAddition(id='pychron.entry1.sample_prep', factory=SamplePrepAction,
                                 path=spath, after='pychron.entry1.sample_edit'),
                  SchemaAddition(id='pychron.entry1.labnumber_entry', factory=LabnumberEntryAction,
                                 path=spath, after='pychron.entry1.sample_prep'),
                  # SchemaAddition(id='pychron.entry1.ir', factory=IRAction,
                  #                path=gpath),
                  SchemaAddition(id='pychron.entry2.make_template', factory=MakeIrradiationTemplateAction,
                                 path=g2path),
                  SchemaAddition(id='pychron.entry1.generate_irradiation_table', factory=GenerateIrradiationTableAction,
                                 path=gpath),
                  SchemaAddition(id='pychron.entry1.import_irradiation_holder', factory=ImportIrradiationHolderAction,
                                 path=gpath),
                  SchemaAddition(id='pychron.entry1.sensitivity_entry', factory=SensitivityEntryAction,
                                 path=gpath),
                  SchemaAddition(id='pychron.entry1.molecular_weight_entry', factory=AddMolecularWeightAction,
                                 path=gpath),
                  SchemaAddition(id='pychron.entry1.flux_monitor', factory=AddFluxMonitorAction,
                                 path=gpath)])]

    def _tasks_default(self):
        return [TaskFactory(id='pychron.entry.irradiation.task',
                            factory=self._labnumber_entry_task_factory,
                            include_view_menu=False),
                TaskFactory(id='pychron.entry.sensitivity.task',
                            factory=self._sensitivity_entry_task_factory,
                            include_view_menu=False),
                TaskFactory(id='pychron.entry.sample.task',
                            factory=self._sample_entry_task_factory,
                            include_view_menu=False),
                TaskFactory(id='pychron.entry.sample.prep.task',
                            factory=self._sample_prep_task_factory,
                            include_view_menu=False),
                # TaskFactory(id='pychron.entry.ir.task',
                #             factory=self._ir_task_factory,
                #             include_view_menu=False)
              ]

    # def _ir_task_factory(self):
    #     from pychron.entry.tasks.ir.task import IRTask
    #     return IRTask(application=self.application)

    def _sample_prep_task_factory(self):
        from pychron.entry.tasks.sample_prep.task import SamplePrepTask

        return SamplePrepTask(application=self.application)

    def _sample_entry_task_factory(self):
        from pychron.entry.tasks.sample.task import SampleEntryTask

        return SampleEntryTask(application=self.application)

    def _labnumber_entry_task_factory(self):
        from pychron.entry.tasks.labnumber.task import LabnumberEntryTask
        return LabnumberEntryTask(application=self.application)

    def _sensitivity_entry_task_factory(self):
        from pychron.entry.tasks.sensitivity.task import SensitivityEntryTask

        return SensitivityEntryTask(application=self.application)

    def _preferences_panes_default(self):
        return [LabnumberEntryPreferencesPane,
                SamplePrepPreferencesPane]

        # ============= EOF =============================================
        # def _task_extensions_default(self):
        # return [TaskExtension(task_id='pychron.entry.labnumber',
        # actions=[SchemaAddition(id='transfer_j',
        # factory=TransferJAction,
        # path='MenuBar/entry.menu/entry.group2'),
        # SchemaAddition(id='import_irradiation',
        # factory=ImportIrradiationAction,
        # path='MenuBar/entry.menu/entry.group2'),
        # SchemaAddition(id='export_irradiation',
        #                                                   factory=ExportIrradiationAction,
        #                                                   path='MenuBar/entry.menu/entry.group2'),
        #                                    # SchemaAddition(id='import_sample_metadata',
        #                                    # factory=ImportSampleMetadataAction,
        #                                    # path='MenuBar/tools.menu', ),
        #
        #                                    SchemaAddition(id='import_samples_from_file',
        #                                                   factory=ImportSamplesAction,
        #                                                   path='MenuBar/entry.menu/entry.group2', ),
        #
        #                                    SchemaAddition(id='generate_tray',
        #                                                   factory=GenerateTrayAction,
        #                                                   path='MenuBar/entry.menu/entry.group2', ),
        #                                    SchemaAddition(id='save_labbook',
        #                                                   factory=SaveLabbookPDFAction,
        #                                                   path='MenuBar/entry.menu/entry.group2'),
        #                                    SchemaAddition(id='make_template',
        #                                                   factory=MakeIrradiationTemplateAction,
        #                                                   path='MenuBar/entry.menu/entry.group2')]),
        #             TaskExtension(actions=[SchemaAddition(id='entry',
        #                                                   factory=lambda: SMenu(id='entry.menu', name='Entry'),
        #                                                   path='MenuBar',
        #                                                   before='tools.menu',
        #                                                   after='view.menu'),
        #                                    SchemaAddition(id='entry_group',
        #                                                   factory=lambda: SGroup(id='entry.group'),
        #                                                   path='MenuBar/entry.menu'),
        #                                    SchemaAddition(id='entry_group2',
        #                                                   factory=lambda: SGroup(id='entry.group2'),
        #                                                   path='MenuBar/entry.menu'),
        #                                    SchemaAddition(id='labnumber_entry',
        #                                                   factory=LabnumberEntryAction,
        #                                                   path='MenuBar/entry.menu/entry.group', absolute_position='first'),
        #                                    SchemaAddition(id='generate_irradiation_table',
        #                                                   factory=GenerateIrradiationTableAction,
        #                                                   path='MenuBar/entry.menu/entry.group'),
        #                                    SchemaAddition(id='import_irradiation_holder',
        #                                                   factory=ImportIrradiationHolderAction,
        #                                                   path='MenuBar/entry.menu/entry.group'),
        #                                    SchemaAddition(id='sensitivity_entry',
        #                                                   factory=SensitivityEntryAction,
        #                                                   path='MenuBar/entry.menu/entry.group'),
        #                                    SchemaAddition(id='molecular_weight_entry',
        #                                                   factory=AddMolecularWeightAction,
        #                                                   path='MenuBar/entry.menu/entry.group'),
        #                                    SchemaAddition(id='molecular_weight_entry',
        #                                                   factory=AddFluxMonitorAction,
        #                                                   path='MenuBar/entry.menu/entry.group')])]
