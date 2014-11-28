## ===============================================================================
# # Copyright 2012 Jake Ross
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# #   http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.
## ===============================================================================
#
##============= enthought library imports =======================
# from traits.api import HasTraits, Button, Str, List, Property, \
#    cached_property, Instance, Dict
# from traitsui.api import View, Item, TableEditor, EnumEditor, \
#    HGroup, VGroup, spring, Group
# from pychron.database.adapters.isotope_adapter import IsotopeAdapter
# from pychron.paths import paths
# import itertools
##============= standard library imports ========================
##============= local library imports  ==========================
#
# class Entry(HasTraits):
#    apply = Button
#    project = Str('a')
#    user = Str('b')
#    material = Str('c')
#
#    materials = Property(depends_on='_materials')
#    _materials = List
#
#    sample = Str('d')
#    sample_auto_increment = Str('@@')
#    auto_increment_cnt = 0
#
#    db = Instance(IsotopeAdapter)
#    _refresh_materials = True
#
#    def _apply_fired(self):
#        db = self.db
#        temp = dict()
#        def add_item(name, params):
#            v = getattr(self, name)
#            if not v is '':
#                adder = getattr(db, 'add_{}'.format(name))
#                temp[name] = adder(v, **params)
#
#        for k in ['project', ('user', 'project'), 'material', ('sample',
#                                                              'material',
#                                                              'project')
#                                                              ]:
#
#            if isinstance(k, tuple):
#                name = k[0]
#                relations = k[1:]
#                add_item(name,
#                         #create a subdict of temp from relations
#                        dict(filter(lambda i:i[0] in relations,
#                                     temp.iteritems()))
#                         )
#            else:
#                add_item(k, dict())
#
# #        db.commit()
#        self._increment_sample()
#        self._load_cache()
#
#    def _increment_sample(self):
#        if not self.sample_auto_increment is '':
#            zeropad = 0
#            alphapad = 0
#            inc = None
#            for si in self.sample_auto_increment:
#                if si == '#':
#                    zeropad += 1
#                elif si == '@':
#                    alphapad += 1
#
#            if alphapad:
#                alpha = [chr(i) for i in range(65, 65 + 26)]
#                inc = self._increment(alpha, alphapad, '@', self.auto_increment_cnt)
#
#            elif zeropad:
#                keys = map(str, range(10))
#                inc = self._increment(keys, zeropad, '#', self.auto_increment_cnt)
#
#            if inc:
#                self.auto_increment_cnt += 1
#                self.sample = '{}-{}'.format(self.sample.split('-')[0],
#                                           inc)
#
#
#    def _increment(self, keys, n, c, ainc):
#        s = self.sample_auto_increment
#        inclist = list(''.join(item)
#                   for item in itertools.product(keys, repeat=n))
#
#        try:
#            incstr = inclist[ainc]
#        except IndexError:
#            inclist = list(''.join(item)
#                       for item in itertools.product(keys, repeat=n + 1))
#
#            incstr = inclist[ainc]
#            s = list(s)
#            s.insert(s.index(c), c)
#            s = ''.join(s)
#
#        self.sample_auto_increment = s
#        s = s.replace(c, '{}')
#        return s.format(*incstr)
#
#    def traits_view(self):
#        v = View(Item('project'),
#                 Item('user'),
#                 HGroup(Item('sample'), Item('sample_auto_increment', label='Auto Increment')),
#                 Item('material', editor=EnumEditor(name='materials',
#                                                    evaluate=lambda x:x
#                                                    )),
#                 Item('apply', show_label=False)
#                 )
#        return v
#
#    def _get_materials(self):
#        return self._get_cached_property('_materials')
#
#    def _load_materials(self):
#        db = self.db
#        if db is not None:
#            return db.get_materials(key='name')
#
#    def _load_cache(self):
#        self._materials = self._load_materials()
#
#    def _get_cached_property(self, name):
#        rname = '_refresh{}'.format(name)
#        if getattr(self, rname):
#            func = getattr(self, '_load{}'.format(name))
#            setattr(self, name, func())
#            setattr(self, rname, False)
# #
#        return getattr(self, name)
#    def _db_default(self):
#        db = IsotopeAdapter(kind='sqlite',
#                            name=paths.isotope_db
#                            )
#        if db.connect():
#            return db
# if __name__ == '__main__':
#    e = Entry()
#    e.configure_traits()
#
## ============= EOF =============================================
