# ===============================================================================
# Copyright 2014 Jake Ross
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
import os


def get_data_dir(op):
    if not os.path.isdir(op):
        op = os.path.join('.', 'data')
    return op


def isotope_db_factory(path, remove=True):
    from pychron.database.adapters.isotope_adapter import IsotopeAdapter
    from pychron.database.orms.isotope.util import Base

    db = IsotopeAdapter()
    # db.verbose_retrieve_query = True
    db.trait_set(kind='sqlite', path=path)
    db.connect()

    if remove and os.path.isfile(db.path):
        os.remove(db.path)

    metadata = Base.metadata
    db.create_all(metadata)


def massspec_db_factory(path, remove=True):
    from pychron.database.adapters.massspec_database_adapter import MassSpecDatabaseAdapter
    from pychron.database.orms.massspec_orm import Base


    if remove and os.path.isfile(path):
        os.remove(path)

    db = MassSpecDatabaseAdapter()
    # db.verbose_retrieve_query = True
    db.trait_set(kind='sqlite', path=path)
    db.connect()

    metadata = Base.metadata
    db.create_all(metadata)

# ============= EOF =============================================



