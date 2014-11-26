# ===============================================================================
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
# ===============================================================================



'''

http://docs.cython.org/pychron/quickstart/build.html

python setup.py build_ext --inplace
'''

from distutils.core import setup
from distutils.extension import Extension

import numpy
from Cython.Distutils import build_ext


ext_modules = [Extension("autocorr", ["autocorr.pyx"],

				        include_dirs=[numpy.get_include(),
                         # pychron_dir
                         ]
				)]

setup(
  name='autocorr',
  cmdclass={'build_ext': build_ext},
  ext_modules=ext_modules
)
