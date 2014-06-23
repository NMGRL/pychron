#===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import HasTraits, List
from traitsui.api import View, Item, ListEditor, InstanceEditor, \
    Group, VGroup
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.hardware.flag import Flag, TimedFlag
from pychron.viewable import Viewable

class FlagManager(Viewable):
    flags = List(Flag)
    timed_flags = List(TimedFlag)
    valve_flags = List(Flag)

    def add_flag(self, f):
        self.flags.append(f)

    def add_timed_flag(self, f):
        self.timed_flags.append(f)

    def add_valve_flag(self, f):
        self.valve_flags.append(f)

    def traits_view(self):
        v = View(
                 VGroup(
                     self._flag_item_factory('flags', 'Flags'),
                     self._flag_item_factory('timed_flags', 'Timed Flags'),
                     self._flag_item_factory('valve_flags', 'Valve Flags')),
                 title='Flag Manager',
                 width=300,
                 handler=self.handler_klass,
                 resizable=True)
        return v

    def _flag_item_factory(self, name, label):
        return Group(Item(name, show_label=False,
                      style='readonly',
                      editor=ListEditor(editor=InstanceEditor(editable=True),
                                        style='custom',
                      )),
                     show_border=True,
                     label=label)


from traits.api import Button
class Demo(HasTraits):
    test = Button
    def traits_view(self):
        return View(Item('test'))

    def _test_fired(self):
        fm = FlagManager()
        fm.flags = [Flag('ObamaPipetteFlag'),
                    Flag('JanPipetteFlag')]
        fm.timed_flags = [TimedFlag('ObamaPipetteFlag'),
                          TimedFlag('JanPipetteFlag')]

        fm.timed_flags[0].set(100)
        fm.edit_traits()

if __name__ == '__main__':
#    fm = FlagManager()
#    fm.flags = [Flag('ObamaPipetteFlag'),
#                Flag('JanPipetteFlag')]
#    fm.timed_flags = [TimedFlag('ObamaPipetteFlag'),
#                      TimedFlag('JanPipetteFlag')]
#
#
#    fm.configure_traits()
    Demo().configure_traits()
#============= EOF =============================================
