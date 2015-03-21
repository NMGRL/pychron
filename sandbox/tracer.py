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
import sys
def traceit(frame, event, arg):
    if event == "line":
        lineno = frame.f_lineno
        print "line", lineno

    return traceit

def info(v):
    print 'this is the imasfd', v

def main():
    sys.settrace(traceit)
    import imp
    foo = imp.load_source('moo', '/Users/ross/Pychrondata_demo/scripts/test.py')

    foo.__dict__['info'] = info

    foo.main()

if __name__ == '__main__':
    main()
