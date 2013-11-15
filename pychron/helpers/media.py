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
import os
import time

from pychron.paths import paths
from threading import Event, Thread
import wx

def loop_sound(name):
    sound = load_sound(name)
    evt = Event()
    def loop():
        sound.Play(wx.SOUND_ASYNC | wx.SOUND_LOOP)
        while not evt.is_set():
            time.sleep(1)

        if sound.IsOk():
            wx.CallAfter(sound.Stop)

    t = Thread(target=loop)
    t.start()
    return evt

def play_sound(name):
    sound = load_sound(name)
    if sound:
        sound.Play()

def load_sound(name):

    if not name.endswith('.wav'):
        name = '{}.wav'.format(name)

    if name in __SOUNDS__:
        return __SOUNDS__[name]

    sp = os.path.join(paths.bundle_root, 'sounds', name)
    if not os.path.isfile(sp):
        sp = os.path.join(paths.sounds, name)

    if os.path.isfile(sp):
        sound = wx.Sound(sp)
        __SOUNDS__[name] = sound
        return sound

__SOUNDS__ = {}
# DEFAULT_SOUNDS = ['shutter']
# for di in DEFAULT_SOUNDS:
# #    # load sound now so quickly available
# #    load_sound('{}.wav'.format(di))
#    load_sound(di)
#    play_sound(di)
#
# print __SOUNDS__
