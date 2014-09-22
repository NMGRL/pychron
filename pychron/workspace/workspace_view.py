# #===============================================================================
# # Copyright 2014 Jake Ross
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
# #===============================================================================
# from pychron.core.ui import set_qt
#
# set_qt()
#
# #============= enthought library imports =======================
# import os
# from traits.api import Button, List
# from traitsui.api import View, UItem
#
# #============= standard library imports ========================
# #============= local library imports  ==========================
# from traitsui.editors import ListStrEditor
# from traitsui.handler import Controller
# from pychron.workspace.index import IndexAdapter, AnalysisIndex, Base
# from pychron.workspace.workspace import WorkspaceManager
#
#
# class WorkspaceView(Controller):
#     load_history = Button
#     history = List
#
#     def _load_history_fired(self):
#         hs = self.model.get_history()
#         self.history = hs
#
#     def traits_view(self):
#         v = View(UItem('controller.load_history'),
#                  UItem('controller.history', editor=ListStrEditor()),
#                  resizable=True)
#         return v
#
#
# if __name__ == '__main__':
#     root = os.path.expanduser('~')
#     root = os.path.join(root, 'Sandbox', 'workspace')
#     wm = WorkspaceManager()
#     wm.create_repo('test', root, None)
#
#     idx = IndexAdapter(path=os.path.join(root, 'index.db'),
#                        schema=AnalysisIndex)
#     idx.connect()
#
#     idx.create_all(Base.metadata)
#
#     wv = WorkspaceView(model=wm)
#     wv.configure_traits()
# #============= EOF =============================================
#
