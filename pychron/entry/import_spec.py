# ===============================================================================
# Copyright 2016 Jake Ross
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

class Irradiation:
    levels = None
    doses = None


class Level:
    name = None
    positions = None
    production = None
    holder = None
    z = None
    note = None


class Production:
    name = None
    K4039 = None
    K3839 = None
    K3739 = None
    Ca3937 = None
    Ca3837 = None
    Ca3637 = None
    Cl3638 = None
    Ca_K = None
    Cl_K = None


class Position:
    position = None
    sample = None
    identifier = None
    j = None
    j_err = None
    note = None
    weight = None


class Sample:
    project = None
    material = None


class Project:
    name = None
    principal_investigator = None


class ImportSpec:
    irradiation = None

# ============= EOF =============================================
