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


from traits.trait_types import Range

from pychron.core.ui.qt.dial_editor import DialEditor


class Dial(Range):
    def __init__(self, label='',
                 low=0, high=10,
                 width=-1, height=-1,
                 display_value=True,
                 value_format=None,
                 **metadata):
        super(Dial, self).__init__(low=low, high=high, **metadata)
        self.editor = DialEditor(low=low, high=high,
                                 display_value=display_value,
                                 value_format=value_format,
                                 height=height,
                                 width=width,
                                 # label=label,
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
                                 # image_on=image_on,
                                 # image_off=image_off,
                                 # tooltip_off=tooltip_off,
                                 # tooltip_on=tooltip_on,
                                 # width=width,
                                 # height=height,
                                 # view=view
        )


#============= EOF =============================================
