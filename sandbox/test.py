# ===============================================================================
# Copyright 2013 Jake Ross
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
from traits.etsconfig.etsconfig import ETSConfig
ETSConfig.toolkit = 'qt4'

from pychron.database.records.isotope_record import IsotopeRecord
from test.database import isotope_manager_factory
# ============= enthought library imports =======================
# ============= standard library imports ========================
# ============= local library imports  ==========================
@profile
def main(db):
    labn = db.get_labnumber('61311',
#                             options='analyses'
                            )

    print '------------------------- got labnunmber'
    an = labn.analyses[0]
    print '------------------------- got analysis'
    a = IsotopeRecord(_dbrecord=an)
    load(a)
    print '------------------------- loaded'

# @profile
def load(a):
    a.load_isotopes()
    print '------------------------- isotopes loaded'
    a.calculate_age()

if __name__ == '__main__':
    man = isotope_manager_factory()
    db = man.db
    db.connect()

#     db.sess.bind.echo = True

    main(db)
# ============= EOF =============================================
