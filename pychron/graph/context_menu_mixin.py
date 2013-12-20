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
from traits.api import HasTraits
from traitsui.menu import Action, Menu as MenuManager
from pychron.pychron_constants import PLUSMINUS
# from pyface.action.group import Group
# from pyface.action.api import Group, MenuManager

#============= standard library imports ========================
#============= local library imports  ==========================

class ContextMenuMixin(HasTraits):
    use_context_menu = True

    def close_popup(self):
        pass

    def action_factory(self, name, func, **kw):
        """
        """
        a = Action(name=name, on_perform=getattr(self, func),
                   #                   visible_when='0',
                   **kw)

        return a

    def get_contextual_menu_save_actions(self):
        """
        """
        return [
            # ('Clipboard', '_render_to_clipboard', {}),
            ('PDF', 'save_pdf', {}),
            ('PNG', 'save_png', {})]

    def contextual_menu_contents(self):
        """
        """
        save_actions = []
        for n, f, kw in self.get_contextual_menu_save_actions():
            save_actions.append(self.action_factory(n, f, **kw))

        save_menu = MenuManager(name='Save Figure',*save_actions)

        #        if not self.crosshairs_enabled:
        #            crosshairs_action = self.action_factory('Show Crosshairs',
        #                           'show_crosshairs'
        #                           )
        #        else:
        #            crosshairs_action = self.action_factory('Hide Crosshairs',
        #                           'destroy_crosshairs')
        #
        #        export_actions = [
        #                          self.action_factory('Window', 'export_data'),
        #                          self.action_factory('All', 'export_raw_data'),
        #
        #                          ]
        #
        #        export_menu = Menu(name='Export',
        #                         *export_actions)
        contents = [save_menu,]
        c=self.get_child_context_menu_actions()
        if c:
            contents.extend(c)

        # if self.editor_enabled:
        #     pa = self.action_factory('Show Plot Editor', 'show_plot_editor')
        #     pa.enabled = self.selected_plot is not None
        #     contents += [pa]
        #     contents += [self.action_factory('Show Graph Editor', 'show_graph_editor')]

        return contents

    def get_child_context_menu_actions(self):
        return

    def get_contextual_menu(self):
        """
        """
        ctx_menu = MenuManager(*self.contextual_menu_contents())

        return ctx_menu



# class IsotopeContextMenuMixin(ContextMenuMixin):
#     def set_status_omit(self):
#         '''
#             override this method in a subclass
#         '''
#         pass
#
#     def set_status_include(self):
#         '''
#             override this method in a subclass
#         '''
#         pass
#
#     def recall_analysis(self):
#         '''
#             override this method in a subclass
#         '''
#         pass
#
#     def contextual_menu_contents(self):
#
#         contents = super(IsotopeContextMenuMixin, self).contextual_menu_contents()
#         contents.append(self.action_factory('Edit Analyses', 'edit_analyses'))
#         actions = []
#         if hasattr(self, 'selected_analysis'):
#             if self.selected_analysis:
#                 actions.append(self.action_factory('Recall', 'recall_analysis'))
#                 if self.selected_analysis.status == 0:
#                     actions.append(self.action_factory('Omit', 'set_status_omit'))
#                 else:
#                     actions.append(self.action_factory('Include', 'set_status_include'))
#                 actions.append(self.action_factory('Void', 'set_status_void'))
#
#                 contents.append(MenuManager(name='Analysis', *actions))
#
#                 #        contents.append(MenuManager(
#                 #                             self.action_factory('Recall', 'recall_analysis', enabled=enabled),
#                 #                             self.action_factory('Omit', 'set_status_omit', enabled=enabled),
#                 #                             self.action_factory('Include', 'set_status_include', enabled=enabled),
#                 #                             name='Analysis'))
#         return contents


class RegressionContextMenuMixin(ContextMenuMixin):
    def contextual_menu_contents(self):
        contents = super(RegressionContextMenuMixin, self).contextual_menu_contents()
        actions = [
            ('linear', 'cm_linear'),
            ('parabolic', 'cm_parabolic'),
            ('cubic', 'cm_cubic'),
            (u'average {}SD'.format(PLUSMINUS), 'cm_average_std'),
            (u'average {}SEM'.format(PLUSMINUS), 'cm_average_sem')
        ]
        menu = MenuManager(
            *[self.action_factory(name, func) for name, func in actions],
            name='Fit')

        #        contents.append(Menu(
        #                             self.action_factory('Omit', 'set_status'),
        #                             self.action_factory('Include', 'set_status'),
        #                             name=))
        contents.append(menu)
        return contents

#============= EOF =============================================
