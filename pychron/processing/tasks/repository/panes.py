# ===============================================================================
# Copyright 2013 Jake Ross
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
from traitsui.api import View, Item, Group, HGroup, spring, \
    UItem, VGroup, ButtonEditor
from pyface.image_resource import ImageResource
from pyface.tasks.traits_task_pane import TraitsTaskPane
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.paths import paths


class RepositoryPane(TraitsTaskPane):

    def traits_view(self):
        igsn_grp = self._get_igsn()
        geochron_grp = self._get_geochron()

        v = View(
                 VGroup(
#                  VSplit(
                        igsn_grp,
                        geochron_grp
                        )
                 )
        return v

    def _get_igsn(self):
        auth_grp = HGroup('object.igsn.username',
                          'object.igsn.password')
        igsn_grp = Group(
                         auth_grp,
                         Item('object.igsn.url',
                              label='URL'),
                         Item('object.igsn.parent_igsn',
                              label='Parent IGSN'
                              ),
                         HGroup(
                                spring,
                                CustomLabel('object.igsn.display_str',
                                            size=14,
                                            color='green'
                                            ),
                                spring),
                         HGroup(spring,
                                UItem('object.igsn.get_igsn_button',
                                      enabled_when='object.igsn_enabled',
                                      tooltip='Get a new IGSN and associate it to this sample'
                                      )),
                         show_border=True,
                         label='IGSN'
                       )
        return igsn_grp

    def _get_geochron(self):
        auth_grp = HGroup('object.repository.username',
                          'object.repository.password')
        grp = Group(
                    auth_grp,
                    Item('object.repository.url',
                         label='URL'),
                    HGroup(spring,
                           UItem('object.repository.upload_button',
                                 style='custom',
                                 editor=ButtonEditor(image=ImageResource(name='arrow_up.png',
                                                                         search_path=paths.icon_search_path)),
                                 enabled_when='object.repo_enabled',
                                 tooltip='Upload to Geochron database'
                                 )
                           ),
                    show_border=True,
                    label='Geochron'
                    )

        return grp
# ============= EOF =============================================
