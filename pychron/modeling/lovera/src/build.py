#!/usr/bin/python
#===============================================================================
# Copyright 2012 Jake Ross
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

#============= enthought library imports =======================
#============= standard library imports ========================
import subprocess
import os
from os import path
#============= local library imports  ==========================

def ifort_build(name, out):
	subprocess.call(['touch', out])
# 	if path.isfile(name):
# #		subprocess.call(['Ifort', name, out, '-save'])
# 	else:
# 		print 'invalid source file {}'.format(name)

def build(files, is_pychron):
	p = path.join(path.dirname(os.getcwd()), 'bin')
	if not path.exists(p):
		os.mkdir(p)

	for f in files:
		out = '{}_py'.format(f) if is_pychron else f
		print 'building', out
		ifort_build(f, '../bin/{}_test'.format(out))

def main(args):
	files = ['files', 'autoarr', 'autoagemon',
	'autoagefree', 'confint', 'corrfft', 'agesme', 'arrme']

	build(files, args.pychron)

if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser(description='Build MDD fortran source')
	parser.add_argument('-p', '--pychron',
						action='store_true',
						default=False,
						 help='build binaries with _py extension')
	args = parser.parse_args()

	main(args)

#============= EOF =============================================
