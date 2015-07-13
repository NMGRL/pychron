# ===============================================================================
# Copyright 2014 Jake Ross
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
from pyface.constant import YES, NO
from traits.api import Instance
from traitsui.api import View, Item, UItem, Group, VGroup

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.entry.editors.base_editor import ModelView
from pychron.entry.editors.chronology import IrradiationChronology
from pychron.loggable import Loggable


class AddView(ModelView):
    def traits_view(self):
        v = View(VGroup(Item('name'),
                        Group(UItem('chronology', style='custom'),
                              label='Chronology', show_border=True)),
                 title='Add Irradiation',
                 kind='livemodal',
                 buttons=['OK', 'Cancel'],
                 width=500,
                 resizable=True)
        return v


class EditView(ModelView):
    def traits_view(self):
        v = View(VGroup(Item('name'),
                        Group(UItem('chronology', style='custom'),
                              label='Chronology', show_border=True)),
                 title='Edit Irradiation',
                 kind='livemodal',
                 buttons=['OK', 'Cancel'],
                 width=500,
                 resizable=True)
        return v


class IrradiationEditor(Loggable):
    """
        class used to create/edit an irradiation

    """
    chronology = Instance(IrradiationChronology, ())

    def add(self):
        v = AddView(model=self)
        info = v.edit_traits()
        
        while 1:
            if info.result:
                name = self.name
                if not name:
                    if self.confirmation_dialog('No name enter. Would you like to enter one?'):
                        info = v.edit_traits()
                        continue
                    else:
                        break

                if not self.dvc.get_irradiation(name):
                    self._add_irradiation()
                    return name

                else:
                    if self.confirmation_dialog(
                            'Irradiation "{}" already exists. Would you like to try again ?'.format(name)):
                        info = v.edit_traits()
                        continue
                    else:
                        break
            else:
                break

    def edit(self):
        original_name = self.name
        # db = self.dvc.db
        # with db.session_ctx():
        # irrad = db.get_irradiation(original_name)
        # print irrad, original_name

        # chronology = DVCChronology(self.name)
        chronology = self.dvc.get_chronology(self.name)
        self.chronology.set_dosages(chronology.get_doses())
        v = EditView(model=self)
        info = v.edit_traits()
        if info.result:
            if original_name != self.name:
                ret = self.confirmation_dialog('You have changed the irradiation name.\n\n'
                                               'Would you like to rename "{}" to "{}" (Yes) '
                                               'or make a new irradiation "{}" (No)'.format(original_name,
                                                                                            self.name, self.name),
                                               return_retval=True,
                                               cancel=True)
                if ret == YES:
                    print 'asdfadfasd'
                    # irrad.name = self.name
                elif ret == NO:
                    self._add_irradiation()
                else:
                    return

            # irrad.chronology.chronology = self.chronology.make_blob()
            # print self.chronology.get_doses()
            self.dvc.update_chronology(self.name, self.chronology.get_doses())
        return self.name

    def _add_irradiation(self):
        self.debug('add irradiation={}'.format(self.name))

        self.dvc.add_irradiation(self.name, self.chronology.get_doses())

        # db = self.db
        #     with db.session_ctx():
        #         # dbchron = db.add_irradiation_chronology(self.chronology.make_blob())
        #         # db.add_irradiation(self.name, dbchron)
        #         db.add_irradiation(self.name)
        #
        #     self.repo.add_irradiation(self.name)
        #     self.repo.add_chronology(self.name, self.chronology)

# ============= EOF =============================================

