# ===============================================================================
# Copyright 2016 Jake Ross
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
from pyface.tasks.traits_dock_pane import TraitsDockPane
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traits.api import Int, Property
from traitsui.api import View, UItem, HGroup, VGroup, TabularEditor
from traitsui.tabular_adapter import TabularAdapter

from pychron.core.ui.combobox_editor import ComboboxEditor
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.envisage.resources import icon

GREEN_BALL = icon('green_ball')


class BaseAdapter(TabularAdapter):
    columns = [('Added', 'added'), ('Name', 'name')]

    added_image = Property
    added_text = Property
    added_width = Int(50)

    def _get_added_text(self):
        return ''

    def _get_added_image(self):
        return GREEN_BALL if self.item.added else None


class PIAdapter(BaseAdapter):
    pass


class MaterialAdapter(BaseAdapter):
    columns = [('Added', 'added'), ('Name', 'name'), ('Grainsize', 'grainsize')]


class ProjectAdapter(BaseAdapter):
    columns = [('Added', 'added'), ('Name', 'name'), ('PI', 'principal_investigator')]
    principal_investigator_text = Property

    def _get_principal_investigator_text(self):
        return self.item.principal_investigator.name


class SampleAdapter(ProjectAdapter):
    columns = [('Added', 'added'), ('Name', 'name'),
               ('Project', 'project'),
               ('Material', 'material'),
               ('Grainsize', 'grainsize'),
               ('PI', 'principal_investigator')]

    project_text = Property
    material_text = Property
    grainsize_text = Property

    def _get_project_text(self):
        return self.item.project.name

    def _get_principal_investigator_text(self):
        return self.item.project.principal_investigator.name

    def _get_material_text(self):
        return self.item.material.name

    def _get_grainsize_text(self):
        return self.item.material.grainsize


class SampleEntryPane(TraitsTaskPane):
    def traits_view(self):
        pis = VGroup(UItem('_principal_investigators', editor=TabularEditor(adapter=PIAdapter(),
                                                                            refresh='refresh_table')),
                     show_border=True,
                     label='PrincipalInvestigators')

        ms = VGroup(UItem('_materials', editor=TabularEditor(adapter=MaterialAdapter(), refresh='refresh_table')),
                    show_border=True,
                    label='Materials')

        ps = VGroup(UItem('_projects', editor=TabularEditor(adapter=ProjectAdapter(), refresh='refresh_table')),
                    show_border=True,
                    label='Projects')
        ss = VGroup(UItem('_samples', editor=TabularEditor(adapter=SampleAdapter(), refresh='refresh_table')),
                    show_border=True,
                    label='Samples')
        return View(VGroup(pis, ps, ms, ss))


class SampleEditorPane(TraitsDockPane):
    id = 'pychron.entry.sample.editor'
    name = 'Editor'

    help_str = '''
<p>
    <b>Principal Investigator</b><br/>
    Good: Ross or Ross,J<br/>
    <font color='red'>Bad: Jake Ross</font>
</p>
<p>
    <b>Project</b>:<br/>
    Good: ProjectName or IR100<br/>
    <font color='red'>Bad: projectname or Project Name or IR #100</font>
</p>

'''
    def traits_view(self):
        pigrp = HGroup(UItem('principal_investigator',
                             editor=ComboboxEditor(name='principal_investigators',
                                                   use_filter=False)),
                       icon_button_editor('add_principal_investigator_button', 'add',
                                          enabled_when='principal_investigator',
                                          tooltip='Add a principal investigator'),
                       label='PrincipalInvestigator',
                       show_border=True)

        prgrp = HGroup(UItem('project', editor=ComboboxEditor(name='projects',
                                                              use_filter=False)),
                       UItem('generate_project_button', tooltip='Generate a default name for this project'),
                       icon_button_editor('add_project_button', 'add',
                                          enabled_when='project',
                                          tooltip='Add a project'),
                       enabled_when='project_enabled',
                       label='Project',
                       show_border=True)

        mgrp = HGroup(UItem('material', editor=ComboboxEditor(name='materials', use_filter=False)),
                      UItem('grainsize', editor=ComboboxEditor(name='grainsizes', use_filter=False)),
                      icon_button_editor('add_material_button', 'add',
                                         enabled_when='material',
                                         tooltip='Add a material'),
                      label='Material',
                      show_border=True)

        sgrp = VGroup(HGroup(UItem('sample'),
                      icon_button_editor('add_sample_button', 'add',
                                         enabled_when='sample',
                                         tooltip='Add a sample')),
                      VGroup(UItem('note', style='custom'), label='Note', show_border=True),
                      enabled_when='sample_enabled',
                      label='Sample',
                      show_border=True)

        v = View(VGroup(pigrp,
                        prgrp,
                        mgrp,
                        sgrp,
                        CustomLabel('pane.help_str')
                        ))
        return v

# ============= EOF =============================================
