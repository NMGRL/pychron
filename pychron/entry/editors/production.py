# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from traits.api import HasTraits, Instance, Str, Float, Unicode, Bool, on_trait_change
from traitsui.api import View, Item, HGroup, VGroup, UCustom, Tabbed, UItem, Group

# ============= standard library imports ========================
# ============= local library imports  ==========================
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


class EUCustom(UCustom):
    enabled_when = 'editable'


class IrradiationProduction(HasTraits):
    name = Str
    reactor = Str
    note = Str
    last_modified = Str

    dirty = Bool

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
    editable = Bool(False)

    def __init__(self, *args, **kw):
        super(IrradiationProduction, self).__init__(*args, **kw)

        self.__edited__ = dict()
        self.__dirty__ = []

    @on_trait_change('''k+:[value,error],ca+:[value,error],cl+:[value,error],
Ca_K:[value,error],Cl_K:[value,error],note''')
    def _set_dirty(self, obj, name, old, new):
        # print name, new

        if name in self.__edited__:
            old_value = self.__edited__[name]
            if old_value != new:
                self.__dirty__.append(1)
            else:
                if self.__dirty__:
                    self.__dirty__.pop()
        else:
            self.__edited__[name] = old
            # self.__dirty__.append(1)

        self.dirty = bool(self.__dirty__)

    def get_params(self):
        params = {}
        keys = ['k4039', 'k3839', 'k3739',
                'ca3937', 'ca3837', 'ca3637',
                'cl3638']

        for ki in keys:
            obj = getattr(self, ki)

            ki = ki.capitalize()
            params[ki] = obj.value
            params['{}_err'.format(ki)] = obj.error

            # setattr(ip, ki, obj.value)
            # setattr(ip, '{}_err'.format(ki), obj.error)

            # ekeys = ['{}_err'.format(ki) for ki in keys]
            # values = [getattr(self, ki).value for ki in keys]
            # errors = [getattr(self, ki).error for ki in keys]
            # ks = [ki.capitalize() for ki in keys + ekeys]
            # params = dict(zip(ks, values + errors))
            #
        params['Ca_K'] = self.Ca_K.value
        params['Ca_K_err'] = self.Ca_K.error
        params['Cl_K'] = self.Cl_K.value
        params['Cl_K_err'] = self.Cl_K.error
        return params

    def create(self, dbrecord):
        for attr in ('K4039', 'K3839', 'K3739',
                     'Ca3937', 'Ca3837', 'Ca3637',
                     'Cl3638'):
            v = getattr(dbrecord, attr)
            e = getattr(dbrecord, '{}_err'.format(attr))
            obj = getattr(self, attr.lower())
            obj.value = v if v is not None else 0
            obj.error = e if e is not None else 0

        self.Ca_K.value = dbrecord.Ca_K if dbrecord.Ca_K else 0
        self.Ca_K.error = dbrecord.Ca_K_err if dbrecord.Ca_K_err else 0

        self.Cl_K.value = dbrecord.Cl_K if dbrecord.Cl_K else 0
        self.Cl_K.error = dbrecord.Cl_K_err if dbrecord.Cl_K_err else 0

        # if dbrecord.last_modified:
        # self.last_modified=dbrecord.last_modified.strftime('%m-%d-%Y %H:%M:%S')
        # self.note = dbrecord.note or ''

    def traits_view(self):
        kgrp = VGroup(EUCustom('k4039'),
                      EUCustom('k3839'),
                      EUCustom('k3739'),
                      label='K', show_border=True)
        cagrp = VGroup(
            EUCustom('ca3937'),
            EUCustom('ca3837'),
            EUCustom('ca3637'),
            label='Ca', show_border=True)
        clgrp = VGroup(
            EUCustom('cl3638'),
            label='Cl', show_border=True)
        elem_grp = VGroup(
            EUCustom('Ca_K'),
            EUCustom('Cl_K'),
            label='Elemental', show_border=True)

        v = View(
            Tabbed(VGroup(HGroup(kgrp,
                              cagrp),
                       clgrp,
                       elem_grp,
                    label='Ratios'),
                   Group(UItem('note', enabled_when='editable',
                               style='custom'),
                         label='Note')),
            width=300)
        return v

# ============= EOF =============================================

