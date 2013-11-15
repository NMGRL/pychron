##===============================================================================
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
##===============================================================================
#
##============= enthought library imports =======================
# from traits.api import HasTraits, Instance
# from traitsui.api import View, Item
##============= standard library imports ========================
##============= local library imports  ==========================
# from pychron.displays.rich_text_display import RichTextDisplay
#
# class Result(HasTraits):
#    display = Instance(RichTextDisplay)
#    def traits_view(self):
#        v = View(Item('display', show_label=False, style='custom'))
#        return v
# #
# #    def clear(self):
# #        self.display.clear()
# #        self.display._display.SetSelection(0, 0)
#
#    def add(self, obj):
#        d = self.display
#        obj.build_results(d)
#
#    def _display_default(self):
#        import wx
#        color = wx.LIGHT_GREY
# #        color = 'lightgrey'
#        d = RichTextDisplay(bg_color=color,
#                            default_size=14,
#                            default_color='black',
#                            height=150)
#        return d
##============= EOF =============================================
