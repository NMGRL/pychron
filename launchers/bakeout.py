#!/usr/bin/python
#===============================================================================
# Copyright 2011 Jake Ross
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
#===============================================================================

if __name__ == '__main__':
    from helpers import build_version
    build_version('_bakeout', egg_path=True)
    from pychron.envisage.bakedpy_run import launch
    from pychron.helpers.logger_setup import logging_setup

    logging_setup('bakeout', level='DEBUG')
    launch()

# ============= EOF ====================================

# #!/usr/bin/python
##===============================================================================
# # Copyright 2011 Jake Ross
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# #   http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.
##===============================================================================
#
#
# if __name__ == '__main__':
#    from helpers import build_version
#    build_version('_bakeout')
#
# #    from globals import globalv
# #    globalv.show_infos = False
# #    globalv.show_warnings = False
#
# #    from pychron.helpers.logger_setup import logging_setup
#    from pychron.helpers.logger_setup import logging_setup
#    from pychron.bakeout.bakeout_manager import BakeoutManager
#
#    logging_setup('bakeout', level='DEBUG')
#
#    bm = BakeoutManager()
#    bm.load()
#    bm.configure_traits()
#    import os
#    os._exit(0)
#
## ============= EOF ====================================
