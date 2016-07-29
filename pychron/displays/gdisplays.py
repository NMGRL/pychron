# ===============================================================================
# Copyright 2011 Jake Ross
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
# ===============================================================================

# ============= enthought library imports =======================
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.displays.display import ErrorDisplay, DisplayController
from pychron.utils import get_display_size

ds = get_display_size()

gWarningDisplay = DisplayController(
    title='Warnings',
    width=450,
    default_color='red',
    bgcolor='light grey',
    max_blocks=300)

gLoggerDisplay = DisplayController(
    title='Info',
    width=700,
    x=ds.width - 650,
    y=20,
    font_size=10,
    default_color='black',
    bgcolor='light grey',
    max_blocks=300)

gMessageDisplay = DisplayController(
    title='Messages',
    width=480,
    y=100,
    default_color='darkgreen',
    bgcolor='light grey',
    max_blocks=300)

gTraceDisplay = ErrorDisplay(
    title='Error Stack',
    width=825,
    x=(ds.width - 825) / 2,
    y=100,
    default_color='black')

# ============= EOF =============================================
