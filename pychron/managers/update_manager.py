# '''
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
# '''
##============= enthought library imports =======================
# from traits.api import Enum, Str, List, Button, Instance
# from traitsui.api import View, Item, EnumEditor, CustomEditor
#
##============= standard library imports ========================
# import wx
# #from threading import Thread
##============= local library imports  ==========================
# from manager import Manager
# #from pychron.svn.svn_client import SVNClient
# from pyface.timer.api import do_after
# class ProgressBar(object):
#    """ A simple progress bar dialog intended to run in the UI thread """
#
#    parent = Instance(wx.Window)
#    control = Instance(wx.Gauge)
#    direction = Enum('horizontal', 'horizontal', 'vertical')
#
#    def __init__(self, parent, minimum=0, maximum=100, direction='horizontal',
#                 size=(200, -1)):
#        """
#        Constructs a progress bar which can be put into a panel, or optionaly,
#        its own window
#
#        """
#        self._max = maximum
#        self.parent = parent
#
#        style = wx.GA_HORIZONTAL
#        if direction == "vertical":
#            style = wx.GA_VERTICAL
#
#        self.size = size
#        self.style = style
#        self.control = self.factory()
#
#    def factory(self):
#        return wx.Gauge(self.parent, -1, self._max, style=self.style, size=self.size)
#
#    def update(self, value):
#        """
#        Updates the progress bar to the desired value.
#
#        """
#        if self._max == 0:
#            self.control.Pulse()
#        else:
#            self.control.SetValue(value)
#
#        self.control.Update()
#
#    def reset(self):
#        #elf.control.Destroy()
#        #self.control=self.factory()
#        self.control.SetValue(0)
#        self.control.Update()
#
# class UpdateManager(Manager):
#    sites = List
#    site = Str
#
#    test = Button
#
#    svn_client = Instance(SVNClient)
#    version = Str
#    progress_bar = None
#    def isCurrent(self):
#        return self.svn_client.isCurrent()
#
#    def _progress_factory(self, window, editor):
#        panel = wx.Panel(window, -1)
#        sizer = wx.BoxSizer(wx.HORIZONTAL)
#        panel.SetSizer(sizer)
#
#        gauge = ProgressBar(panel, maximum=0)
#        self.progress_bar = gauge
#        sizer.Add(gauge.control)
#
#        return panel
#
#    def _svn_client_default(self):
#        return SVNClient()
#
#    def edit_traits(self, *args, **kw):
#        do_after(200, self._check_for_updates)
#        return super(UpdateManager, self).edit_traits(*args, **kw)
#
#    def traits_view(self):
#        v = View(
#               'test',
#               Item('site', editor=EnumEditor(name='sites')),
#               #Item('status', editor=ProgressEditor(min=0,max=5)),
#               Item('version'),
#               Item('progress_bar', style='custom',
#                    show_label=False,
#                    editor=CustomEditor(factory=self._progress_factory)),
#               resizable=True
#               )
#        return v
#
#    def _site_changed(self):
#        print self.site
#
#    def _test_fired(self):
#        print self.svn_client.isCurrent()
# #        t = Thread(target = self._check_for_updates)
# #        t.start()
#    def _check_for_updates(self):
#        #use pysvn to get version info
#        c = self.svn_client
#        _name, info = c.get_remote_version_file(progress=self.progress_bar)
#        remote_rev = info.last_changed_rev.number
#
#        _name, info = c.get_local_version_file()
#
#        local_rev = info.revision.number
#        if local_rev != remote_rev:
#            self.info('updates required')
#        else:
#            self.info('''no updates available
# remote revision = %i
# local revision = %i
# ''' % (remote_rev, local_rev))
#        return local_rev != remote_rev
#
# if __name__ == '__main__':
#    u = UpdateManager()
#    u.configure_traits()
##============= EOF =============================================
