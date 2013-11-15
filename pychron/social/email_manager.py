##===============================================================================
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
##===============================================================================
#
#
#
##=============enthought library imports=======================
#from traits.api import HasTraits, Str, Enum, Bool, List, Password, Int
#from traitsui.api import View, Item, TableEditor
#from traitsui.table_column import ObjectColumn
#from traitsui.extras.checkbox_column import CheckboxColumn
##============= standard library imports ========================
#import os
#import smtplib
#from email.mime.multipart import MIMEMultipart
#from email.mime.text import MIMEText
#
##============= local library imports  ==========================
#from pychron.managers.manager import Manager
#from pychron.paths import paths
#from smtplib import SMTPServerDisconnected
#class User(HasTraits):
#    name = Str
#    email = Str
#    email_enabled = Bool
#    multruns_notify = Bool
#    level = Enum(0, 1, 2)
#
#
#    telephone = Str
#
#
#    def edit_view(self):
#        return View('name',
#                    'email',
#                    'level',
#                    'multruns_notify',
#                    'telephone'
#
#                    )
#class EmailManager(Manager):
#    users = List(User)
#
#    outgoing_server = Str
#    port = Int(587)
#    sender = Str('Pychron')
#    server_username = Str
#    server_password = Password
#
#    _server = None
#    def __init__(self, *args, **kw):
#        super(EmailManager, self).__init__(*args, **kw)
#        self.load_users_file()
#
#
#    def traits_view(self):
#        v = View(Item('users', show_label=False,
#                    editor=TableEditor(columns=[ObjectColumn(name='name'),
#                                                CheckboxColumn(name='multruns_notify'),
#                                                CheckboxColumn(name='email_enabled')
#                                                ],
#                                       orientation='vertical',
#                                       edit_view='edit_view',
#                                       show_toolbar=True,
#                                       row_factory=self.row_factory
#                                       )
#                    ),
#               width=500,
#               height=400,
#               resizable=True
#               )
#        return v
#
#    def row_factory(self):
#        u = User(name='moo')
#        self.users.append(u)
#
#    def get_emails(self, level):
#        return [u.email for u in self.users if u.email_enabled and u.level <= level]
#
#    def get_notify_emails(self):
#        return [u for u in self.users if u.email_enabled and u.multruns_notify]
#
#    def _message_factory(self, text, level, subject='!Pychron Alert!'):
#        msg = MIMEMultipart()
#        msg['From'] = self.sender  # 'nmgrl@gmail.com'
#        msg['To'] = ', '.join(self.get_emails(level))
#        msg['Subject'] = subject
#
#        msg.attach(MIMEText(text))
#        return msg
#
#    def connect(self):
#        if self._server is None:
#            try:
#                server = smtplib.SMTP(self.outgoing_server, self.port)
#                server.ehlo()
#                server.starttls()
#                server.ehlo()
#
#                server.login(self.server_username, self.server_password)
#                self._server = server
#            except SMTPServerDisconnected:
#                self.warning('SMTPServer not properly configured')
#
#        return self._server
#
#    def broadcast(self, text, level=0, subject=None):
#
#        recipients = self.get_emails(level)
#        if recipients:
#            msg = self._message_factory(text, level, subject)
#            server = self.connect()
#            if server:
#                self.info('Broadcasting message to {}'.format(','.join(recipients)))
#                server.sendmail(self.sender, recipients, msg.as_string())
#                server.close()
#
#    def add_user(self, **kw):
#        u = User(**kw)
#        self.users.append(u)
#
##    def get_configuration(self):
##        p =
##        config = ConfigParser()
##        config.read(p)
##
##        return config
#
#    def load_users_file(self, *args, **kw):
#        path = os.path.join(paths.setup_dir, 'users.cfg')
#        config = self.configparser_factory()
#        config.read(path)
#
#        for user in config.sections():
#            kw = dict(name=user)
#            for opt, func in [('email', None), ('level', 'int'), ('email_enabled', 'boolean')]:
#                if func is None:
#                    func = config.get
#                else:
#                    func = getattr(config, 'get{}'.format(func))
#
#                kw[opt] = func(user, opt)
#            self.users.append(User(**kw))
#
#    def save_users(self):
#        path = os.path.join(paths.setup_dir, 'users.cfg')
#        self.info('saving users to {}'.format(path))
#        config = self.configparser_factory()
#
#        for user in self.users:
#            name = user.name
#            config.add_section(name)
#            for attr in ['email', 'level', 'email_enabled', 'multruns_notify']:
#                config.set(name, attr, getattr(user, attr))
##
##            config.set(name, 'email', user.email)
##            config.set(name, 'level', user.level)
##            config.set(name, 'email_enabled', user.email_enabled)
##            config.set(name, 'multruns_notify', user.email_enabled)
#
#        with open(path, 'w') as f:
#            config.write(f)
#
#
#if __name__ == '__main__':
#    em = EmailManager()
#    em.users = [
#              User(name='foo',
#                   email='jirhiker@gmail.com'
#                   ),
#              User(name='moo',
#                   email='nmgrlab@gmail.com'
#                   )
#              ]
#    em.broadcast('ffoooo')
#    # em.configure_traits()
##============= EOF =====================================
