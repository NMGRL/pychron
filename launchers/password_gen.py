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

#============= enthought library imports =======================
import argparse
import getpass
#============= standard library imports ========================
#============= local library imports  ==========================

version_id = '_experiment'
from helpers import build_version
'''
    set_path=True inserts the pychron source directory into the PYTHONPATH
    necessary if you are launching from commandline or eclipse(?). 
    Use false (default) if your are launching from a standalone bundle. 
'''
build_version(version_id, set_path=True)

from pychron.envisage.credentials import Credentials

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate a password')
    parser.add_argument('-p', '--password',
                        action='store'
                        )
    args = parser.parse_args()

    pwd = args.password
    cancel = False
    if not pwd:
        pwd1 = ''
        pwd2 = None
        while pwd1 != pwd2:
            pwd1 = getpass.getpass('Password: ')
            pwd2 = getpass.getpass('Re-enter Password: ')
            if pwd1 != pwd2:
                if raw_input('Passwords did not match. Try again. [y/n]? ') == 'y':
                    continue
                else:
                    cancel = True
                    break

        if not cancel:
            pwd = pwd1

    if pwd:
        hpass, salt = Credentials.generate_hashed_password(pwd)
        print 'Hex password: {}'.format(hpass)
        print 'Hex salt: {}'.format(salt)


#    args = sys.argv[1:]
#    if args:
#        if args[0]:
# #            c = Credentials(password=args[0])
#            hpass, salt = Credentials.generate_hashed_password(args[0])
#            print hpass
#            print salt
#            print c.verify(hpass, salt)
# ============= EOF =============================================
