# ===============================================================================
# Copyright 2018 ross
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
from chaco.api import Legend
from enable.font_metrics_provider import font_metrics_provider
from numpy import zeros_like, array
from traits.api import Bool, Int


class ExplicitLegend(Legend):
    bgcolor = "transparent"
    inside = Bool(False)
    xoffset = Int(0)
    yoffset = Int(0)

    def get_preferred_size(self):
        """
        Computes the size and position of the legend based on the maximum size of
        the labels, the alignment, and position of the component to overlay.
        """
        # Gather the names of all the labels we will create
        if len(self.plots) == 0:
            return [0, 0]

        # plot_names, visible_plots = list(map(list, list(zip(*sorted(self.plots.items())))))
        plot_names, visible_plots = [list(a) for a in zip(*sorted(self.plots.items()))]

        label_names, names = list(zip(*self.labels))
        if len(label_names) == 0:
            if len(self.plots) > 0:
                label_names = plot_names
            else:
                self._cached_labels = []
                self._cached_label_sizes = []
                self._cached_label_names = []
                self._cached_visible_plots = []
                self.outer_bounds = [0, 0]
                return [0, 0]

        if self.hide_invisible_plots:
            visible_labels = []
            visible_plots = []
            for key, name in self.labels:
                # If the user set self.labels, there might be a bad value,
                # so ensure that each name is actually in the plots dict.
                if key in self.plots:
                    val = self.plots[key]
                    # Rather than checking for a list/TraitListObject/etc., we just check
                    # for the attribute first
                    if hasattr(val, "visible"):
                        if val.visible:
                            visible_labels.append(name)
                            visible_plots.append(val)
                    else:
                        # If we have a list of renderers, add the name if any of them are
                        # visible
                        for renderer in val:
                            if renderer.visible:
                                visible_labels.append(name)
                                visible_plots.append(val)
                                break
            label_names = visible_labels

        # Create the labels
        labels = [self._create_label(text) for text in label_names]

        # For the legend title
        if self.title_at_top:
            labels.insert(0, self._create_label(self.title))
            label_names.insert(0, "Legend Label")
            visible_plots.insert(0, None)
        else:
            labels.append(self._create_label(self.title))
            label_names.append(self.title)
            visible_plots.append(None)

        # We need a dummy GC in order to get font metrics
        dummy_gc = font_metrics_provider()
        label_sizes = array([label.get_width_height(dummy_gc) for label in labels])

        if len(label_sizes) > 0:
            max_label_width = max(label_sizes[:, 0])
            total_label_height = (
                sum(label_sizes[:, 1]) + (len(label_sizes) - 1) * self.line_spacing
            )
        else:
            max_label_width = 0
            total_label_height = 0

        legend_width = (
            max_label_width
            + self.icon_spacing
            + self.icon_bounds[0]
            + self.hpadding
            + 2 * self.border_padding
        )
        legend_height = total_label_height + self.vpadding + 2 * self.border_padding

        self._cached_labels = labels
        self._cached_label_sizes = label_sizes
        self._cached_label_positions = zeros_like(label_sizes)
        self._cached_label_names = label_names
        self._cached_visible_plots = visible_plots

        if "h" not in self.resizable:
            legend_width = self.outer_width
        if "v" not in self.resizable:
            legend_height = self.outer_height
        return [legend_width, legend_height]

    def _draw_as_overlay(self, gc, view_bounds=None, mode="normal"):
        """Draws the overlay layer of a component.

        Overrides PlotComponent.
        """
        # Determine the position we are going to draw at from our alignment
        # corner and the corresponding outer_padding parameters.  (Position
        # refers to the lower-left corner of our border.)

        # First draw the border, if necesssary.  This sort of duplicates
        # the code in PlotComponent._draw_overlay, which is unfortunate;
        # on the other hand, overlays of overlays seem like a rather obscure
        # feature.

        with gc:
            if self.inside:
                if self.align == "ur":
                    self.x -= 5
                    self.y -= 5
                elif self.align == "ul":
                    self.x += 5
                    self.y -= 5
            else:
                self.y += self.height + 5

            self.x += self.xoffset
            self.y += self.yoffset
            gc.clip_to_rect(int(self.x), int(self.y), int(self.width), int(self.height))
            edge_space = self.border_width + self.border_padding
            icon_width, icon_height = self.icon_bounds

            icon_x = self.x + edge_space
            text_x = icon_x + icon_width + self.icon_spacing
            y = self.y2 - edge_space

            if self._cached_label_positions is not None:
                if len(self._cached_label_positions) > 0:
                    self._cached_label_positions[:, 0] = icon_x

            for i, label_name in enumerate(self._cached_label_names):
                # Compute the current label's position
                label_height = self._cached_label_sizes[i][1]
                y -= label_height
                self._cached_label_positions[i][1] = y

                # Try to render the icon
                icon_y = y + (label_height - icon_height) / 2
                # plots = self.plots[label_name]
                plots = self._cached_visible_plots[i]
                render_args = (gc, icon_x, icon_y, icon_width, icon_height)

                try:
                    if isinstance(plots, list) or isinstance(plots, tuple):
                        # TODO: How do we determine if a *group* of plots is
                        # visible or not?  For now, just look at the first one
                        # and assume that applies to all of them
                        if not plots[0].visible:
                            # TODO: the get_alpha() method isn't supported on the Mac kiva backend
                            # old_alpha = gc.get_alpha()
                            old_alpha = 1.0
                            gc.set_alpha(self.invisible_plot_alpha)
                        else:
                            old_alpha = None
                        if len(plots) == 1:
                            plots[0]._render_icon(*render_args)
                        else:
                            self.composite_icon_renderer.render_icon(
                                plots, *render_args
                            )
                    elif plots is not None:
                        # Single plot
                        if not plots.visible:
                            # old_alpha = gc.get_alpha()
                            old_alpha = 1.0
                            gc.set_alpha(self.invisible_plot_alpha)
                        else:
                            old_alpha = None
                        plots._render_icon(*render_args)
                    else:
                        old_alpha = None  # Or maybe 1.0?

                    icon_drawn = True
                except:
                    icon_drawn = self._render_error(*render_args)

                if icon_drawn:
                    # Render the text
                    gc.translate_ctm(text_x, y)
                    gc.set_antialias(0)
                    self._cached_labels[i].draw(gc)
                    gc.set_antialias(1)
                    gc.translate_ctm(-text_x, -y)

                    # Advance y to the next label's baseline
                    y -= self.line_spacing
                if old_alpha is not None:
                    gc.set_alpha(old_alpha)

        return


# ============= EOF =============================================
