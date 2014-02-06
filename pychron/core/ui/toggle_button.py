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

#============= standard library imports ========================
#============= local library imports  ==========================


from traits.trait_types import Event

from pychron.core.ui.qt.toggle_button_editor import ToggleButtonEditor


class ToggleButton(Event):
    def __init__(self, label='',
                 image_on=None,
                 image_off=None,
                 tooltip_on='',
                 tooltip_off='',
                 width=32, height=32,
                 **metadata):
        self.editor = ToggleButtonEditor(
            label=label,
            # filename=filename,
            # tooltip=tooltip,
            # toggle=toggle,
            # toggle_state=toggle_state,
            # toggle_filename=toggle_filename,
            # toggle_tooltip=toggle_tooltip,
            # toggle_label=toggle_label,
            # orientation=orientation,
            # width_padding=width_padding,
            # height_padding=height_padding,
            image_on=image_on,
            image_off=image_off,
            tooltip_off=tooltip_off,
            tooltip_on=tooltip_on,
            width=width,
            height=height,
            # view=view
        )

        super(ToggleButton, self).__init__(**metadata)

#============= EOF =============================================
