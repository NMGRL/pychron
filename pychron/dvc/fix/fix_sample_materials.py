# ===============================================================================
# Copyright 2022 ross
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
from itertools import groupby
from operator import attrgetter

from pychron.dvc.dvc_helper import get_dvc

DRY = True


def main():
    dvc = get_dvc()
    dvc.connect()
    with dvc.session_ctx() as sess:
        ms = dvc.get_materials()
        key = attrgetter("name")

        def gkey(x):
            return x.grainsize or ""

        for mname, mss in groupby(sorted(ms, key=key), key=key):
            for gname, gs in groupby(sorted(mss, key=gkey), key=gkey):
                first = next(gs)
                mss = list(gs)
                dest_material_id = first.id
                print(mname, f"{first.id}, {first.name} {first.grainsize}")
                for mi in sorted(mss, key=attrgetter("id")):
                    print(f"  {dest_material_id} <-- {mi.id}, {mi.name} {mi.grainsize}")
                    for s in dvc.get_samples_by_material(mi.id):
                        print(f"    setting sample {s} material to {dest_material_id}")
                        if not DRY:
                            s.materialID = dest_material_id

                    if not DRY:
                        sess.delete(mi)

                        sess.commit()
                        sess.flush()


if __name__ == "__main__":
    main()
# ============= EOF =============================================
