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
from traits.api import HasTraits, Str, Property, Bool
from traitsui.api import View, Item, Handler, HGroup, spring, HTMLEditor
import apptools.sweet_pickle as pickle
#============= standard library imports ========================
import os
from pyface.timer.do_later import do_later
#============= local library imports  ==========================
class VersionInfo(HasTraits):
    '''
    '''
    major = Str
    minor = Str
    version = Property(transient=True)
    text = Str

    def _get_version(self):
        return '.'.join((self.major, self.minor))


class VersionInfoHandler(Handler):
    '''
    '''
    def closed(self, info, is_ok):
        if info.object.dismiss_notification:
            info.object.dump()


class VersionInfoDisplay(HasTraits):
    '''
    '''
    message = Property
    local_version = Str
    local_path = Str
    src_path = Str
    dismiss_notification = Bool(False)
    version_info = VersionInfo

    def _get_message(self):
        args = ()
        vi = self.version_info
        msg = \
            '''<h2>Version {major}.{minor}</h2>
                <h3>Previous Version {previous_version}
<p><font color="red">file or directory change required</font></p>
<p>{text}</p>'''
        return msg.format(major=vi.major, minor=vi.minor, text=vi.text,
                          previous_version=self.local_version, *args)

    def traits_view(self):
        v = View(
            Item('message', style='custom', editor=HTMLEditor(),
                 show_label=False),
            HGroup(spring, Item('dismiss_notification')),
            kind='modal',
            handler=VersionInfoHandler,
            buttons=['OK'],
            width=300,
            height=300,
            title='Version Info',
            )

        return v

    def dump(self):
        '''
        '''
        with open(self.local_path, 'wb') as f:
            pickle.dump(self.version_info, f)

    def check(self):
        '''
        '''
        local_info = None
        major = None
        minor = None

        # get the local version info

        if os.path.isfile(self.local_path):
            with open(self.local_path, 'rb') as f:
                local_info = pickle.load(f)

        if os.path.isfile(self.src_path):

        # get the version_info associated with the pychron code

            with open(self.src_path, 'rb') as f:
                f.readline()
                line = f.readline()
                major = line.split('=')[1].strip()

                line = f.readline()
                minor = line.split('=')[1].strip()

                self.version_info = VersionInfo(major=major,
                        minor=minor)
                f.readline()
                p = []
                ps = []
                new_para = False
                for line in f:
                    line = line.strip()
                    if new_para:
                        ps.append(p)
                        p = []
                        new_para = False

                    if len(line) > 0:
                        if len(p) == 0 and line[0] == '#':
                            line = '<h5><u>{}</u></h5>'.format(line[1:])
                        p.append(line)
                    else:
                        new_para = True

                self.version_info.text = \
                    ''.join(['<p>{}</p>'.format(pj) for pj in
                            [' '.join(pi) for pi in ps if len(pi) > 0]])

        if minor is not None and major is not None:
            mismatch = True
            if local_info is not None:
                mismatch = local_info.version != '.'.join((major,
                        minor))

            if mismatch:
                if local_info is not None:
                    self.local_version = local_info.version
            elif local_info is None:
                do_later(self.edit_traits, kind='modal')
#============= EOF =============================================
