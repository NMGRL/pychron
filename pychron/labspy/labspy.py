# ===============================================================================
# Copyright 2014 Jake Ross
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


from pychron.core.ui import set_qt
from pychron.paths import paths, build_directories
build_directories()

set_qt()
# ============= enthought library imports =======================
from traits.api import Str, Instance
# ============= standard library imports ========================
from datetime import datetime
import random
import time
import hashlib
import os
from mako.template import Template
import yaml
# ============= local library imports  ==========================
from pychron.loggable import Loggable
from pychron.pychron_constants import SCRIPT_NAMES
from pychron.repo.repository import SFTPRepository

EXPERIMENT_ATTRS = ('username', 'mass_spectrometer',
                    'extract_device', 'name', 'start_timestamp')



class LabspyUpdater(Loggable):
    spectrometer_name = Str

    # use webdav instead
    repo = Instance(SFTPRepository, ())

    def push(self):
        _, exps = self._load_experiment()
        _, ans = self._load_analyses()
        ctx = {'experiments': exps, 'analyses': ans}
        ctx['last_update'] = datetime.now().isoformat()

        spec_ctx =[]
        for spec, name in (('jan','Jan'), ('obama','Obama'),('nmgrl_map','MAP')):
            fans =[ai for ai in ans if ai['mass_spectrometer'].lower()==spec]
            sctx={'name':name, 'usage': len(fans)}
            for atype in ('unknown','air','blank_unknown','blank_air'):
                aa = [ai for ai in fans if ai['analysis_type']==atype]
                sctx['n{}s'.format(atype)]=len(aa)
            spec_ctx.append(sctx)

        # print spec_ctx
        ctx['spectrometer_usages'] = spec_ctx

        nco2 =len([ai for ai in ans if ai['extract_device'].lower()=='co2'])
        ndiode =len([ai for ai in ans if ai['extract_device'].lower()=='diode'])
        nuv =len([ai for ai in ans if ai['extract_device'].lower()=='uv'])
        ctx['extract_device_usages'] = [{'name':'CO2', 'usage':nco2},
                                        {'name':'Diode', 'usage':ndiode},
                                        {'name':'UV', 'usage':nuv}]
        # print ctx
        txt = Template(self._load_template()).render(**ctx)
        # root = os.path.join(self.labspy_root, '_build')
        # if not os.path.isdir(root):
        #     os.mkdir(root)

        path = os.path.join(paths.labspy_dir, 'index.html')
        with open(path, 'w') as fp:
            fp.write(txt)

        # print path
        self.repo.add_file(path)

        self.repo.add_file(self.ans_ctx_path)

    def add_experiment(self, exp):
        path, yl = self._load_experiment()
        if not yl:
            yl = []
        d = {k: getattr(exp, k) for k in EXPERIMENT_ATTRS}
        d['status'] = 'Running'
        yl.insert(0, d)
        yl = yl[:4]

        with open(path, 'w') as fp:
            yaml.dump(yl, fp, default_flow_style=False)

        self.repo.add_file(self.exp_ctx_path)
        self.push()

    def update_experiment(self, exp, err_msg):

        path, yl = self._load_experiment()

        def hfunc(yi):
            h = hashlib.md5()
            for ai in EXPERIMENT_ATTRS:
                h.update(yi[ai])
            return h.hexdigest()

        hkey = hfunc(exp)
        yy = next((yi for yi in yl if hfunc(yi) == hkey))
        yy['status'] = err_msg or 'Successful'

        self._dump_experiment(yl)
        self.repo.add_file(self.exp_ctx_path)
        self.push()

    def add_run(self, run):
        path = self.ans_ctx_path
        yl = None
        if os.path.isfile(path):
            with open(path, 'r') as fp:
                yl = yaml.load(fp)

        if not yl:
            yl = []
        yl.insert(0, self._make_analysis(run))
        yl = yl[:50]

        with open(path, 'w') as fp:
            yaml.dump(yl, fp, default_flow_style=False)
        self.repo.add_file(self.ans_ctx_path)
        self.push()

    def _load_analyses(self):
        path = self.ans_ctx_path

        #pull from repo
        self.repo.retrieveFile(os.path.basename(path), path)

        yl = None
        if os.path.isfile(path):
            with open(path, 'r') as fp:
                yl = yaml.load(fp)

        return path, yl or []

    def _load_experiment(self):
        path = self.exp_ctx_path

        #pull from repo
        self.repo.retrieveFile(os.path.basename(path), path)

        yl = []
        if os.path.isfile(path):
            with open(path, 'r') as fp:
                yl = yaml.load(fp)
        return path, yl or []

    def _dump_experiment(self, d):
        with open(self.exp_ctx_path, 'w') as fp:
            yaml.dump(d, fp, default_flow_style=False)

    def _load_template(self):
        with open(self.template_path) as fp:
            return fp.read()

    @property
    def template_path(self):
        for root in paths.labspy_template_search_path:
            for di in ('', 'templates'):
                path = os.path.join(root, di, 'labspy_main.html')
                if os.path.isfile(path):
                    return path
    @property
    def ans_ctx_path(self):
        root = paths.labspy_context_dir
        path = os.path.join(root, 'labspy_analyses_context.yaml')
        return path

    @property
    def exp_ctx_path(self):
        root = paths.labspy_context_dir
        path = os.path.join(root, 'labspy_experiment_context.yaml')
        return path

    def _make_analysis(self, run):
        spec = run.spec

        d = {k: getattr(spec, k) for k in ('record_id', 'analysis_type', 'sample',
                                           'extract_value', 'duration', 'cleanup', 'position',
                                           'comment', 'material', 'project',
                                           'mass_spectrometer',
                                           'extract_device', 'experiment_name')}

        d['date'] = spec.analysis_timestamp.strftime('%m-%d-%Y %H:%M:%S')
        d['timestamp'] = time.mktime(spec.analysis_timestamp.timetuple())
        d['runtime'] = spec.analysis_timestamp.strftime('%H:%M')
        for si in SCRIPT_NAMES:
            d[si] = getattr(spec, si)

        return d


if __name__ == '__main__':
    l = LabspyUpdater()
    # l.labspy_root = os.path.join(os.path.expanduser('~'), 'Programming', 'git', 'gh-pages-labspy')
    l.repo.trait_set(username='documentation',
                     password='Argon',
                     host='129.138.12.131',
                     root='/Users/documentation/Sites/labspy')

    class Exp(object):
        username = 'foo'
        status = ''
        def __init__(self):
            dt = datetime.now()
            self.start_timestamp = dt.strftime('%m-%d-%Y %H:%M:%S')
            self.mass_spectrometer = random.choice(('jan','obama','nmgrl_map'))
            self.extract_device = random.choice(('co2','diode','uv'))


    class Spec(object):
        record_id = '12345-01A'

        sample = 'bar'

        comment = 'this is a comment'
        material = 'Sanidine'
        project = 'Labspy'
        mass_spectrometer = ''
        extract_device = ''

        measurement_script = 'm'
        post_measurement_script = 'pm'
        post_equilibration_script = 'pe'
        extraction_script = 'ex'
        experiment_name = ''
        def __init__(self):
            self.analysis_timestamp = datetime.now()
            self.extract_value = random.randint(0, 100)
            self.duration = random.randint(0, 100)
            self.cleanup = random.randint(0, 100)
            self.position = random.randint(0, 10)
            self.analysis_type = random.choice(('unknown','air',
                                                'blank_unknown','blank_air'))
            self.project = random.choice(('Foo','Bar','Moo','Bat'))

    class Ans(object):
        def __init__(self):
            self.spec = Spec()

    # for i in range(4):
    i=0
    exp = Exp()
    exp.name='Experiment {:02n}'.format(i)
    l.add_experiment(exp)
    for j in range(2):
        a = Ans()
        a.spec.mass_spectrometer = exp.mass_spectrometer
        a.spec.experiment_name = exp.name
        a.spec.extract_device = exp.extract_device
        l.add_run(a)
        print 'add run'

    time.sleep(1)

# ============= EOF =============================================
    # def _labspy_root_changed(self, new):
    #     if new:
    #         if os.path.isdir(new):
    #             self.repo.open_repo(new)
    #         else:
    #             if self.use_git:
    #                 self.repo.clone('https://github.com/NMGRL/labspy')
    #                 self.repo.create_remote('https://github.com/NMGRL/labspy')
    #                 self.repo.checkout_branch('gh-pages')
    #
    #         self.enabled = True
# class enabled_dec(object):
#     def __init__(self):
#         pass
#
#     def __call__(self, method):
#         def wrapper(obj, *args, **kw):
#             if obj.enabled:
#                 method(obj, *args, **kw)
#
#         return wrapper

# class LabspyUpdater(Loggable):
#     spectrometer_name = Str
#     labspy_root = Str
#     enabled = False
#     backend = 'ftp'
#
#     def __init__(self, *args, **kw):
#         super(LabspyUpdater, self).__init__(*args, **kw)
#         if self.backend == 'git':
#             self.repo = GitRepoManager()
#         else:
#             self.repo = SFTPRepository()
#
#     @property
#     def use_git(self):
#         return self.backend == 'git'
#
#     @enabled_dec()
#     def push(self):
#         if self.use_git:
#             self.repo.push()
#         else:
#             _, exps = self._load_experiment()
#             _, ans = self._load_analyses()
#             ctx = {'experiments': exps, 'analyses': ans}
#             ctx['last_update'] = datetime.now().isoformat()
#
#             njan = len([ai for ai in ans if ai['mass_spectrometer'].lower()=='jan'])
#             nobama = len([ai for ai in ans if ai['mass_spectrometer'].lower()=='obama'])
#             nmap = len([ai for ai in ans if ai['mass_spectrometer'].lower()=='nmgrl_map'])
#
#             ctx['spectrometer_usages'] = [{'name': 'Jan', 'usage': njan},
#                                           {'name': 'Obama', 'usage': nobama},
#                                           {'name': 'MAP', 'usage': nmap}]
#
#             nco2 =len([ai for ai in ans if ai['extract_device'].lower()=='co2'])
#             ndiode =len([ai for ai in ans if ai['extract_device'].lower()=='diode'])
#             nuv =len([ai for ai in ans if ai['extract_device'].lower()=='uv'])
#             ctx['extract_device_usages'] = [{'name':'CO2', 'usage':nco2},
#                                             {'name':'Diode', 'usage':ndiode},
#                                             {'name':'UV', 'usage':nuv},
#                                             ]
#             txt = Template(self._load_template()).render(**ctx)
#             root = os.path.join(self.labspy_root, '_build')
#             if not os.path.isdir(root):
#                 os.mkdir(root)
#
#             path = os.path.join(root, 'index.html')
#             with open(path, 'w') as fp:
#                 fp.write(txt)
#             print path
#             # self.repo.add_file(path)
#
#     @enabled_dec()
#     def add_experiment(self, exp):
#         path, yl = self._load_experiment()
#         if not yl:
#             yl = []
#         d = {k: getattr(exp, k) for k in EXPERIMENT_ATTRS}
#         d['status'] = 'Running'
#         yl.insert(0, d)
#         yl = yl[-4:]
#
#         with open(path, 'w') as fp:
#             yaml.dump(yl, fp, default_flow_style=False)
#
#         if self.use_git:
#             self.repo.add(path, commit=True)
#
#         self.push()
#
#     @enabled_dec()
#     def update_experiment(self, exp, err_msg):
#
#         path, yl = self._load_experiment()
#
#         def hfunc(yi):
#             h = hashlib.md5()
#             for ai in EXPERIMENT_ATTRS:
#                 h.update(yi[ai])
#             return h.hexdigest()
#
#         hkey = hfunc(exp)
#         yy = next((yi for yi in yl if hfunc(yi) == hkey))
#         yy['status'] = err_msg or 'Successful'
#
#         self._dump_experiment(yl)
#
#         if self.use_git:
#             self.repo.truncate_repo()
#         self.push()
#
#     @enabled_dec()
#     def add_run(self, run):
#         path = self.ans_ctx_path
#         yl = None
#         if os.path.isfile(path):
#             with open(path, 'r') as fp:
#                 yl = yaml.load(fp)
#
#         if not yl:
#             yl = []
#         yl.insert(0, self._make_analysis(run))
#         yl = yl[-50:]
#
#         with open(path, 'w') as fp:
#             yaml.dump(yl, fp, default_flow_style=False)
#
#         if self.use_git:
#             self.repo.add(path, commit=True)
#
#         self.push()
#
#     def _load_analyses(self):
#         path = self.ans_ctx_path
#         yl = None
#         if os.path.isfile(path):
#             with open(path, 'r') as fp:
#                 yl = yaml.load(fp)
#
#         return path, yl or []
#
#     def _load_experiment(self):
#         path = self.exp_ctx_path
#         yl = []
#         if os.path.isfile(path):
#             with open(path, 'r') as fp:
#                 yl = yaml.load(fp)
#         return path, yl
#
#     def _dump_experiment(self, d):
#         with open(self.exp_ctx_path, 'w') as fp:
#             yaml.dump(d, fp, default_flow_style=False)
#
#     def _load_template(self):
#         with open(self.template_path) as fp:
#             return fp.read()
#
#     @property
#     def template_path(self):
#         for root in paths.labspy_template_search_path:
#             for di in ('', 'templates'):
#                 path = os.path.join(root, di, 'labspy_main.html')
#                 if os.path.isfile(path):
#                     return path
#     @property
#     def ans_ctx_path(self):
#         root = self.repo.path
#         path = os.path.join(root, '_data', 'labspy_analyses_context.yaml')
#         return path
#
#     @property
#     def exp_ctx_path(self):
#         root = self.repo.path
#         path = os.path.join(root, '_data', 'labspy_experiment_context.yaml')
#         return path
#
#     def _make_analysis(self, run):
#         spec = run.spec
#
#         d = {k: getattr(spec, k) for k in ('record_id', 'analysis_type', 'sample',
#                                            'extract_value', 'duration', 'cleanup', 'position',
#                                            'comment', 'material', 'project',
#                                            'mass_spectrometer',
#                                            'extract_device', 'experiment_name')}
#
#         d['date'] = spec.analysis_timestamp.strftime('%m-%d-%Y %H:%M:%S')
#         d['timestamp'] = time.mktime(spec.analysis_timestamp.timetuple())
#         d['runtime'] = spec.analysis_timestamp.strftime('%H:%M')
#         for si in SCRIPT_NAMES:
#             d[si] = getattr(spec, si)
#
#         return d
#
#     def _labspy_root_changed(self, new):
#         if new:
#             if os.path.isdir(new):
#                 self.repo.open_repo(new)
#             else:
#                 if self.use_git:
#                     self.repo.clone('https://github.com/NMGRL/labspy')
#                     self.repo.create_remote('https://github.com/NMGRL/labspy')
#                     self.repo.checkout_branch('gh-pages')
#
#             self.enabled = True


