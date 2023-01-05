# ===============================================================================
# Copyright 2012 Jake Ross
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
from chaco.array_data_source import ArrayDataSource
from traits.api import List, Callable
from traitsui.menu import Action, Menu as MenuManager

from pychron.core.helpers.formatting import floatfmt
from pychron.graph.tools.point_inspector import PointInspector

# from pychron.pipeline.plot.inspector_item import AnalysisInspectorItem
from pychron.pychron_constants import PLUSMINUS


class AnalysisPointInspector(PointInspector):
    analyses = List
    value_format = Callable
    additional_info = Callable
    _selected_indices = List
    index_tag = None
    single_point = False
    include_x = False

    def contextual_menu_contents(self):
        """ """
        actions = (
            Action(name="Recall", on_perform=self._recall_analysis),
            Action(name="Set tag", on_perform=self._set_tag),
            Action(name="Set Omit", on_perform=self._set_omit),
            Action(name="Set Invalid", on_perform=self._set_invalid),
        )
        return actions

    def get_contextual_menu(self):
        ctx_menu = MenuManager(*self.contextual_menu_contents())
        return ctx_menu

    def normal_right_down(self, event):
        print("nsdo", event, self.current_position)
        self._selected_indices = []
        if self.current_position:
            inds = self.get_selected_index()
            print("insdf", inds)
            if inds is not None:
                self._selected_indices = list(inds)
                self._show_menu(event)

    def _set_tag(self):
        ai = self.analyses[0]
        ans = [self.analyses[i] for i in self._selected_indices]
        ai.trigger_tag(ans)

    def _set_omit(self):
        ai = self.analyses[0]
        ans = [self.analyses[i] for i in self._selected_indices]
        ai.trigger_omit(ans)

    def _set_invalid(self):
        ai = self.analyses[0]
        ans = [self.analyses[i] for i in self._selected_indices]
        ai.trigger_invalid(ans)

    def _recall_analysis(self):
        for i in self._selected_indices:
            ai = self.analyses[i]
            ai.trigger_recall()

    def _show_menu(self, event):
        self.get_contextual_menu()

        control = event.window.control

        menu_manager = self.get_contextual_menu()
        menu = menu_manager.create_menu(control, None)

        menu.show()
        menu_manager.destroy()
        event.handled = True

    def assemble_lines(self):

        lines = []
        if self.current_position:
            inds = self.get_selected_index()

            if inds is not None:
                n = len(inds)
                component = self.component
                ys = component.value.get_data()
                xs = component.index.get_data()

                for i, ind in enumerate(inds):
                    analysis = self.analyses[ind]

                    rid = analysis.record_id
                    name = component.container.y_axis.title
                    for tag in ("<sub>", "</sub>", "<sup>", "</sup>"):
                        name = name.replace(tag, "")

                    xname = component.container.x_axis.title
                    for tag in ("<sub>", "</sub>", "<sup>", "</sup>"):
                        xname = xname.replace(tag, "")

                    y = ys[ind]
                    x = xs[ind]

                    if hasattr(component, "yerror"):
                        try:
                            yerror = component.yerror
                            if isinstance(yerror, ArrayDataSource):
                                yerror = yerror.get_data()

                            ye = yerror[ind]
                            pe = self.percent_error(y, ye)
                            if self.value_format:
                                ye = self.value_format(ye)
                            if self.value_format:
                                y = self.value_format(y)

                            y = "{} {} {} {}".format(y, PLUSMINUS, ye, pe)
                        except IndexError as e:
                            print("asdf", e)

                    else:
                        if self.value_format:
                            y = self.value_format(y)

                    info = [
                        "Analysis= {} UUID({})".format(rid, analysis.display_uuid),
                        "Tag= {}".format(analysis.tag),
                        "{}= {}".format(name, y),
                    ]

                    if self.include_x:

                        if hasattr(component, "xerror"):
                            try:
                                xerror = component.xerror
                                if isinstance(xerror, ArrayDataSource):
                                    xerror = xerror.get_data()

                                xe = xerror[ind]
                                pe = self.percent_error(x, xe)

                                x = "{} {} {} {}".format(floatfmt(x), PLUSMINUS, xe, pe)
                            except IndexError as e:
                                print("asdf", e)
                        else:
                            x = floatfmt(x)

                        info.append("{}= {}".format(xname, x))

                    if analysis.comment:
                        info.insert(1, "Comment= {}".format(analysis.comment[:20]))

                    if hasattr(analysis, "status_text"):
                        info.insert(1, "Status= {}".format(analysis.status_text))
                    lines.extend(info)
                    if self.additional_info is not None:
                        ad = self.additional_info(ind, xs[ind], ys[ind], analysis)
                        if isinstance(ad, (list, tuple)):
                            lines.extend(ad)
                        else:
                            lines.append(ad)

                    if i < n - 1:
                        lines.append("--------")

        return lines


# ============= EOF =============================================
