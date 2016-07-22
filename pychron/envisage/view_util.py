# ===============================================================================
# Copyright 2015 Jake Ross
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

__views__ = []


def open_view(obj, **kw):
    info = obj.edit_traits(**kw)
    add_view(info)
    info.on_trait_change(destroyed, 'destroyed')

    return info


def destroyed(obj, name, old, new):
    obj.on_trait_change(destroyed, 'destroyed', remove=True)
    __views__.remove(obj)


def add_view(info):
    __views__.append(info)


def close_views():
    global __views__
    if __views__:
        # print len(__views__)
        for v in __views__:
            # print 'dispose {}'.format(v)
            try:
                v.dispose(abort=True)
            except BaseException, e:
                print v, e
    __views__ = None


def report_view_stats():
    if __views__:
        print 'report view stats'
        print '-------------------------'
        for v in __views__:
            print v
        print '-------------------------'

# ============= EOF =============================================
