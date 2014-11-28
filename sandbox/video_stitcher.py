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

#============= standard library imports ========================
#============= local library imports  ==========================
import os
def stitch(path, fps=2, name_filter='%03d.jpg', output=None):
    import subprocess
    if output is None:
        output = os.path.join(path, '{}.mp4'.format(path))

    if os.path.exists(output):
        os.remove(output)
#         return

    ffmpeg = '/usr/local/bin/ffmpeg'
    frame_rate = '{}'.format(fps)
    codec = '{}'.format('x264')  # H.264
    path = '{}'.format(os.path.join(path, name_filter))

    subprocess.call([ffmpeg, '-qscale', '1', '-r', frame_rate, '-i', path, output,
#                      '-codec', codec
                     ])


if __name__ == '__main__':
#     args = sys.argv[1:]
#     print args
    p = '/Users/ross/Pychrondata_demo/data/snapshots/scan6'
    stitch(p)

# ============= EOF =============================================
