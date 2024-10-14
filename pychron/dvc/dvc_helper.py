# ===============================================================================
# Copyright 2023 ross
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
import os

from pyface.message_dialog import warning

from pychron.dvc.dvc import DVC
from pychron.paths import paths


def get_dvc(**kw):
    conn = dict(
        host=os.environ.get("ARGONSERVER_HOST"),
        username=os.environ.get("ARGONSERVER_DB_USER"),
        password=os.environ.get("ARGONSERVER_DB_PWD"),
        name="pychrondvc",
        kind="mysql",
    )
    conn.update(**kw)

    paths.build("~/PychronDirs/PychronDev")
    meta_name = "NMGRLMetaData"
    dvc = DVC(bind=False, organization="NMGRLData", meta_repo_name=meta_name)
    paths.meta_root = os.path.join(paths.dvc_dir, dvc.meta_repo_name)
    dvc.db.trait_set(**conn)
    if not dvc.initialize():
        warning(None, "Failed to initialize DVC")
        return

    dvc.meta_repo.smart_pull()
    return dvc


# ============= EOF =============================================
