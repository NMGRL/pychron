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
## ============= enthought library imports =======================
# from traits.api import HasTraits, Any, Button, Property, Int, Str, List, Bool
# from traitsui.api import View, Item, ListStrEditor, HGroup
## ============= standard library imports ========================
## ============= local library imports  ==========================
#
#
# class SetSelector(HasTraits):
#    experiment_executor = Any
#    experiment_sets = List  # Instance('pychron.experiment_set.ExperimentSet')
#    add_button = Button('+')
#    delete_button = Button('-')
#    names = Property(depends_on='experiment_executor.experiment_sets')
#
#    selected_index = Int
#    selected = Str
#    editable = Bool(True)
#    def _get_names(self):
#        return ['Queue {}'.format(i + 1)
#                for i in range(len(self.experiment_executor.experiment_queues))]
#
# #        print 'asdffds', ['Set {}'.format(i + 1) for i in range(len(self.experiment_sets))]
#
#    def _add_button_fired(self):
#        exp = self.experiment_executor
#        exp.new_experiment_queue(clear=False)
#        i = 0
#        while 1:
#            ni = len(self.names) + 1 + i
#            na = 'Set{}'.format(ni)
#            if na in self.names:
#                i += 1
#            else:
#                break
# #        self.names.append(na)
# #        self.trait_set(selected_index=ni - 1, trait_change_notify=False)
#
#    def _delete_button_fired(self):
#        if self.selected_index:
#            si = self.selected_index
#        else:
#            si = len(self.names) - 1
# #        self.names.pop(si)
#        self.experiment_executor.experiment_queues.pop(si)
#
#    def _selected_index_changed(self):
#        if self.selected_index >= 0:
#            em = self.experiment_executor
#            em.experiment_set = em.experiment_queues[self.selected_index]
#
#    def traits_view(self):
#        v = View(
#
#                 Item('names',
#
#                                show_label=False,
#                                editor=ListStrEditor(
#                                                     editable=False,
#                                                     selected_index='selected_index',
#                                                     operations=[])),
#                 HGroup(
#                        Item('add_button',
#                             width= -40,
#                             show_label=False, defined_when='editable'),
#                        Item('delete_button',
#                             width= -40,
#                             show_label=False, defined_when='editable')
#                        ),
#                 )
#        return v
#
## ============= EOF =============================================
