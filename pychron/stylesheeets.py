# ===============================================================================
# Copyright 2015 Jake Ross
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
# ============= standard library imports ========================
# ============= local library imports  ==========================
# adapted from https://github.com/ColinDuquesnoy/QDarkStyleSheet

# cedce7 0%,#596a72

default_sheet = '''
QLineEdit {font-size: 10px}
QGroupBox {

    /*background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #f7fbfc,
                                      stop: 1 #add9e4);*/
    /*background-color: qlinear-gradient(x1: 0, y1: 0, x2: 0, y2: 1,
    /*x3: 0, y3: 10,
                                       stop: 0 #f7fbfc,
                                       stop: 1 #d9edf2,
                                       /*stop: 2 #add9e4
                                       );*/
    border: 2px solid gray;
    border-radius: 5px;
    padding-top: 0.25em;
    margin-top: 1.25ex; /* leave space at the top for the title */
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left; /* position at the top center */
    color: #000000;
}
QComboBox {font-size: 10px}

'''

# ============= EOF =============================================
