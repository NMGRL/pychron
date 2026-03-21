# ===============================================================================
# Copyright 2024 ross
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
from pychron.loggable import Loggable
from traits.api import Instance


class SeedDatabase(Loggable):
    dvc = Instance("pychron.dvc.dvc.DVC")

    def seed(self):
        self.info("Seeding database")
        self._seed()
        self.info("Database seeded")

    def _seed(self):
        with self.dvc.session_ctx():
            self._seedirradiationspositions()

    def _seedirradiationspositions(self):
        self.info("Seeding irradiations and positions")
        dvc = self.dvc
        db = dvc.db
        positions = (
            ("NoIrradiation", "A", "1", "ba-01-N"),
            ("NoIrradiation", "A", "2", "a-01-N"),
            ("NoIrradiation", "A", "3", "bu-CC-N"),
            ("NoIrradiation", "A", "4", "dg"),
        )
        n = len(positions)
        for i, (irradiation, level, hole, identifier) in enumerate(positions):
            dbpos = db.get_irradiation_position(irradiation, level, hole)
            if not dbpos:
                dbpos = db.add_irradiation_position(irradiation, level, hole)

            # if the identifier is set then don't overwrite
            if not dbpos.identifier:
                # add the flux file to the index only on the last iteration
                dvc.meta_repo.update_flux(
                    irradiation, level, hole, identifier, 0, 0, add=i == n - 1
                )

        # add to database
        # db.add_irradiation_level(
        #     self.name, self.irradiation, self.selected_tray, prname, 0, self.level_note
        # )
        #
        # # add to repository
        # meta_repo = self.dvc.meta_repo
        # meta_repo.add_level(self.irradiation, self.name)
        # meta_repo.update_productions(self.irradiation, self.name, prname)
        # meta_repo.add_production_to_irradiation(self.irradiation, prname, {})
        #
        # meta_repo.commit("Added level {} to {}".format(self.name, self.irradiation))
        # self.info('Seeding irradiations and positions complete')


# ============= EOF =============================================
