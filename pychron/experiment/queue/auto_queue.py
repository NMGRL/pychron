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
from traits.api import Str, Any
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.loggable import Loggable


class AutoQueue(Loggable):
    db = Any
    load_name = Str

    def generate(self, ):
        def gen():
            db = self.db
            load_name = self.load_name
            with db.session_ctx():
                dbload = self.db.get_loadtable(load_name)
                for poss in dbload.loaded_positions:
                    # print poss
                    ln_id = poss.lab_identifier
                    dbln = self.db.get_labnumber(ln_id, key='id')
                    yield dbln.identifier, str(poss.position)

        return gen

            # for ln, poss in groupby(dbload.loaded_positions,
            #                         key=lambda x: x.lab_identifier):
            #     dbln = self.db.get_labnumber(ln, key='id')
            #     sample = ''
            #     if dbln and dbln.sample:
            #         sample = dbln.sample.name
            #     dbirradpos = dbln.irradiation_position
            #     dblevel = dbirradpos.level
            #
            #     irrad = dblevel.irradiation.name
            #     level = dblevel.name
            #     irradpos = dbirradpos.position
            #     irradiation = '{} {}{}'.format(irrad, level, irradpos)

                # pos = []
                # for pi in poss:
                #     pid = str(pi.position)
                    # item = self.canvas.scene.get_item(pid)
                    # if item:
                    #     item.fill = True
                    #     item.add_labnumber_label(
                    #         dbln.identifier, ox=-10, oy=-10,
                    #         visible=self.show_labnumbers)
                    #
                    #     oy = -10 if not self.show_labnumbers else -20
                    #     wt = '' if pi.weight is None else str(pi.weight)
                    #     item.add_weight_label(wt, oy=oy, visible=self.show_weights)
                    #     item.weight = pi.weight
                    #     item.note = pi.note
                    #     item.sample = sample
                    #     item.irradiation = irradiation

                    # pos.append(pid)

                # if group_labnumbers:
                #     self._add_position(ln, pos)
                # else:
                #     for pi in pos:
                #         self._add_position(ln, [pi])


# ============= EOF =============================================



