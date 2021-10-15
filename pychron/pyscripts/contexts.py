# ===============================================================================
# Copyright 2019 ross
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


class CTXObject(object):
    def update(self, ctx):
        self.__dict__.update(**ctx)


class EXPObject(CTXObject):
    pass


class CMDObject(CTXObject):
    pass


class MeasurementCTXObject(object):
    def create(self, yd):
        for k in (
                "baseline",
                "multicollect",
                "peakcenter",
                "equilibration",
                "whiff",
                "peakhop",
        ):
            try:
                c = CTXObject()
                c.update(yd[k])
                setattr(self, k, c)
            except KeyError:
                pass

# ============= EOF =============================================
