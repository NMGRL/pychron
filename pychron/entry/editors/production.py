#===============================================================================
# Copyright 2014 Jake Ross
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
from traits.api import HasTraits, Instance, Str, Float, Unicode
from traitsui.api import View, Item, HGroup, VGroup, UCustom

#============= standard library imports ========================
#============= local library imports  ==========================
class ProductionValue(HasTraits):
    value = Float
    error = Float
    name = Unicode

    def traits_view(self):
        v = View(HGroup(Item('name', style='readonly'),
                        Item('value'),
                        Item('error'),
                        show_labels=False))
        return v


class IrradiationProduction(HasTraits):
    reactor=Str

    # K interferences
    k4039 = Instance(ProductionValue, (), {'name': 'K 40/39'})
    k3839 = Instance(ProductionValue, (), {'name': 'K 38/39'})
    k3739 = Instance(ProductionValue, (), {'name': 'K 37/39'})


    #Ca interferences
    ca3937 = Instance(ProductionValue, (), {'name': 'Ca 39/37'})
    ca3837 = Instance(ProductionValue, (), {'name': 'Ca 38/37'})
    ca3637 = Instance(ProductionValue, (), {'name': 'Ca 36/37'})

    #Cl interference
    cl3638 = Instance(ProductionValue, (), {'name': 'Cl 36/38'})

    # elemental production ratio
    Ca_K = Instance(ProductionValue, (), {'name': 'Ca/K'})
    Cl_K = Instance(ProductionValue, (), {'name': 'Cl/K'})

    def create(self, dbrecord):
        for attr in ('K4039','K3839','K3739',
                    'Ca3937','Ca3837','Ca3637',
                    'Cl3638'):
            v=getattr(dbrecord, attr)
            e=getattr(dbrecord, '{}_err'.format(attr))
            obj=getattr(self, attr.lower())
            obj.value=v
            obj.error=e

        self.Ca_K.value = dbrecord.Ca_K
        self.Ca_K.error = dbrecord.Ca_K_err

        self.Cl_K.value = dbrecord.Cl_K
        self.Cl_K.error = dbrecord.Cl_K_err

    def traits_view(self):
        kgrp = VGroup(UCustom('k4039'),
                      UCustom('k3839'),
                      UCustom('k3739'),
                      label='K', show_border=True)
        cagrp = VGroup(
            UCustom('ca3937'),
            UCustom('ca3837'),
            UCustom('ca3637'),
            label='Ca', show_border=True)
        clgrp = VGroup(
            UCustom('cl3638'),
            label='Cl', show_border=True)
        elem_grp = VGroup(
            UCustom('Ca_K'),
            UCustom('Cl_K'),
            label='Elemental', show_border=True)

        v = View(
            VGroup(
                # HGroup(Item('name'),
                #        Item('db_name',
                #             show_label=False,
                #             editor=CheckListEditor(name='names'))
                # ),
                VGroup(HGroup(kgrp,
                       cagrp),
                       clgrp,
                       elem_grp)),
            width=300,
            # resizable=True,
            # buttons=[Action(name='Save', action='save',
            #                 #                                enabled_when='object.save_enabled'
            # ),
            #          'Cancel'
            # ],
            # handler=self.handler_klass,
            # title='Production Ratio Input'
        )
        return v

#============= EOF =============================================

