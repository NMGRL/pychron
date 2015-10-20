## ===============================================================================
## Copyright 2011 Jake Ross
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##   http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
## ===============================================================================
#
## =============enthought library imports=======================
#from traits.api import HasTraits, Instance, Str, Password
#from traitsui.api import View, Item
#from pychron.managers.manager import Manager
#from threading import Thread
#
## ============= standard library imports ========================
## ============= local library imports  ==========================
## def sudo(command, password=None, prompt="Enter password "):
##
##    import pexpect
##
##    if not password:
##        import getpass
##        password = getpass.getpass(prompt)
##
##    command = "sudo " + command
##    child = pexpect.spawn(command)
##    child.logfile = sys.stdout
##    child.expect(['Password:', pexpect.EOF, pexpect.TIMEOUT])
##    try:
##        child.sendline(password)
##    except OSError:
##        pass
##    child.expect(pexpect.EOF)
##    # is this necessary?
##    child.close()
#
#'''
#credentials
#
#usr= nmgrl
#pwd=Argon4039
#
#'''
#try:
#    import twitter
#except ImportError, e:
#    print 'install twitter', e
#
#
#class Crediential(HasTraits):
#    user_name = Str('root')
#    password = Password()
#    def traits_view(self):
#        v = View('user_name',
#               'password',
#               )
#        return v
#
#class TwitterManager(Manager):
#    tapi = None
#    credientials = Instance(Crediential, ())
#    def install_view(self):
#        v = View(Item('credientials', show_label=False,
#                    style='custom'),
#               kind='livemodal',
#               buttons=['OK', 'Cancel']
#               )
#        return v
#
#    def __init__(self, *args, **kw):
#        super(TwitterManager, self).__init__(*args, **kw)
##        self.get_twitter()
#        try:
#            self.tapi = twitter.Api(consumer_key='8mdnnhVEhOlT7Xu8Mg',
#                               consumer_secret='IzMqOxjSemTXyjZ8VCelFpUXdrhD77E74SV6mdrl7E',
#                               access_token_key='27101038-lzzwYplffclywtSAWnfbuB3ovrnPgmqkWMFqO2jvf',
#                               access_token_secret='BOea1U7aUoQXJEQ1CldvrK5RkjLImfXGls6PbuQw'
#                               )
#        except NameError, e:
# print 'exception', e
##    def get_twitter(self):
#        # check for dependencies:
##        try:
##
##            import twitter
##        except ImportError:
##            self.warning('Could not import python-twitter. Is it installed?')
##
##            info = self.edit_traits(view='install_view')
##            if info.result:
##                cmd = '/Library/Frameworks/Python.framework/Versions/Current/bin/easy_install python-twitter'
##                #cmd='/Library/Frameworks/Python.framework/Versions/Current/bin/easy_install crcmod'
## #                cmd='pwd'
##                err = sudo(cmd,
##                     password=self.credientials.password)
## #
##                #activation not working so gonna have to require a restart
##                #python-twitter requires setuptools and I think thats causing the problem
##
##                if err is None:
##                    msg = 'python-twitter successfully installed. restart required '
##                    self.info(msg)
##                    information(None, msg)
##                else:
##                    msg = 'python-twitter failed to install. '
##                    self.info(msg)
##                    information(None, msg)
##
##                sys.exit()
#
#
##                import pkg_resources
## #                dist=pkg_resources.Distribution.from_location('/Library/Frameworks/Python.framework/Versions/7.1/lib/python2.7/site-packages',
## #                                                         'python_twitter-0.8.2-py2.7.egg'
## #                                                       )
## #                pkg_resources.working_set.add(dist)
##                dist=pkg_resources.get_distribution('python-twitter')
##                print dist
##                dist.activate()
## #                reload(pkg_resources)
##
##                import crcmod
##                print crcmod
#
##        self.tapi = twitter.Api(consumer_key='8mdnnhVEhOlT7Xu8Mg',
##                               consumer_secret='IzMqOxjSemTXyjZ8VCelFpUXdrhD77E74SV6mdrl7E',
##                               access_token_key='27101038-lzzwYplffclywtSAWnfbuB3ovrnPgmqkWMFqO2jvf',
##                               access_token_secret='BOea1U7aUoQXJEQ1CldvrK5RkjLImfXGls6PbuQw'
##                               )
#
#    def verify(self):
#        if self.tapi is not None:
#            print self.tapi.VerifyCredentials()
#
#
#    def post(self, msg):
#
#        if self.tapi is not None:
#            def _post():
#                try:
#                    self.tapi.PostUpdate(msg)
#                    self.info('Posted - {}'.format(msg))
#                except twitter.TwitterError:
#                    pass
#
#            t = Thread(target=_post)
#            t.start()
#
#
#if __name__ == '__main__':
#    m = TwitterManager()
#    m.get_twitter()
##    class App(HasTraits):
##    #    man=Instance(TwitterManager,())
##        test = Button
##        def _test_fired(self):
##            tm = TwitterManager()
##        def traits_view(self):
##            return View(Item('test'))
#    m.verify()
#    m.post('test mesgffff')
##    m=App()
##    m.configure_traits()
#
## ============= EOF ==============================================
