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
import base64
import hashlib
import os
import shutil
import struct
from datetime import datetime

from git.exc import GitCommandError
from traits.api import Instance, Bool, Str
from uncertainties import std_dev, nominal_value

from pychron.dvc import dvc_dump, analysis_path
from pychron.dvc.dvc_analysis import META_ATTRS, EXTRACTION_ATTRS, PATH_MODIFIERS
from pychron.experiment.automated_run.persistence import BasePersister
# from pychron.experiment.classifier.isotope_classifier import IsotopeClassifier
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.paths import paths
from pychron.pychron_constants import DVC_PROTOCOL, LINE_STR, NULL_STR


def format_repository_identifier(project):
    return project.replace('/', '_').replace('\\', '_')


def spectrometer_sha(src, defl, gains):
    sha = hashlib.sha1()
    for d in (src, defl, gains):
        for k, v in sorted(d.items()):
            sha.update(k)
            sha.update(str(v))

    return sha.hexdigest()


class DVCPersister(BasePersister):
    active_repository = Instance(GitRepoManager)
    dvc = Instance(DVC_PROTOCOL)
    use_isotope_classifier = Bool(False)
    # isotope_classifier = Instance(IsotopeClassifier, ())
    stage_files = Bool(True)
    default_principal_investigator = Str
    _positions = None

    def per_spec_save(self, pr, repository_identifier=None, commit=False, commit_tag=None):
        self.per_spec = pr

        if repository_identifier:
            self.initialize(repository_identifier, False)

        self.pre_extraction_save()
        self.pre_measurement_save()
        self.post_extraction_save()
        self.post_measurement_save(commit=commit, commit_tag=commit_tag)

    def initialize(self, repository, pull=True):
        """
        setup git repos.

        repositories are guaranteed to exist. The automated run factory clones the required projects
        on demand.

        :return:
        """
        self.debug('^^^^^^^^^^^^^ Initialize DVCPersister {} pull={}'.format(repository, pull))

        self.dvc.initialize()

        repository = format_repository_identifier(repository)
        self.active_repository = repo = GitRepoManager()

        root = os.path.join(paths.repository_dataset_dir, repository)
        repo.open_repo(root)

        remote = 'origin'
        if repo.has_remote(remote) and pull:
            self.info('pulling changes from repo: {}'.format(repository))
            self.active_repository.pull(remote=remote, use_progress=False)

    def pre_extraction_save(self):
        pass

    def post_extraction_save(self):

        per_spec = self.per_spec
        rblob = per_spec.response_blob  # time vs measured response
        oblob = per_spec.output_blob  # time vs %output
        sblob = per_spec.setpoint_blob  # time vs requested

        if rblob:
            rblob = base64.b64encode(rblob)
        if oblob:
            oblob = base64.b64encode(oblob)
        if sblob:
            sblob = base64.b64encode(sblob)

        obj = {'request': rblob,  # time vs
               'response': oblob,
               'sblob': sblob,
               'snapshots': per_spec.snapshots,
               'videos': per_spec.videos}

        pid = per_spec.pid
        if pid:
            obj['pid'] = pid

        for e in EXTRACTION_ATTRS:
            v = getattr(per_spec.run_spec, e)
            obj[e] = v

        ps = []
        for i, pp in enumerate(per_spec.positions):
            pos, x, y, z = None, None, None, None
            if isinstance(pp, tuple):
                if len(pp) == 2:
                    x, y = pp
                elif len(pp) == 3:
                    x, y, z = pp
            else:
                pos = pp
                try:
                    ep = per_spec.extraction_positions[i]
                    x = ep[0]
                    y = ep[1]
                    if len(ep) == 3:
                        z = ep[2]
                except IndexError:
                    self.debug('no extraction position for {}'.format(pp))
            pd = {'x': x, 'y': y, 'z': z, 'position': pos, 'is_degas': per_spec.run_spec.identifier == 'dg'}
            ps.append(pd)

        self._positions = ps
        obj['positions'] = ps

        hexsha = self.dvc.get_meta_head()
        obj['commit'] = str(hexsha)

        path = self._make_path(modifier='extraction')
        dvc_dump(obj, path)

    def pre_measurement_save(self):
        pass

    def post_measurement_save(self, commit=True, commit_tag='COLLECTION'):
        """
        save
            - analysis.json
            - analysis.monitor.json

        check if unique spectrometer.json
        commit changes
        push changes
        :return:
        """
        self.debug('================= post measurement started')
        ret = True

        ar = self.active_repository

        # save spectrometer
        spec_sha = self._get_spectrometer_sha()
        spec_path = os.path.join(ar.path, '{}.json'.format(spec_sha))
        if not os.path.isfile(spec_path):
            self._save_spectrometer_file(spec_path)

        # self.dvc.meta_repo.save_gains(self.per_spec.run_spec.mass_spectrometer,
        #                               self.per_spec.gains)

        # save analysis

        if not self.per_spec.timestamp:
            timestamp = datetime.now()
        else:
            timestamp = self.per_spec.timestamp

        # check repository identifier before saving
        # will modify repository to NoRepo if repository_identifier does not exist
        self._check_repository_identifier()

        self._save_analysis(timestamp)

        # save monitor
        self._save_monitor()

        # save peak center
        self._save_peak_center(self.per_spec.peak_center)

        # stage files
        dvc = self.dvc
        if self.stage_files:
            if commit:
                try:
                    ar.smart_pull(accept_their=True)

                    # commit the reset of the files
                    paths = [spec_path, ] + [self._make_path(modifier=m) for m in PATH_MODIFIERS]

                    for p in paths:
                        if os.path.isfile(p):
                            ar.add(p, commit=False)
                        else:
                            self.debug('not at valid file {}'.format(p))

                    # commit files
                    ar.commit('<{}>'.format(commit_tag))

                    # commit default data reduction
                    add = False
                    p = self._make_path('intercepts')
                    if os.path.isfile(p):
                        ar.add(p, commit=False)
                        add = True

                    p = self._make_path('baselines')
                    if os.path.isfile(p):
                        ar.add(p, commit=False)
                        add = True

                    if add:
                        ar.commit('<ISOEVO> default collection fits')

                    for pp, tag, msg in (('blanks', 'BLANKS',
                                          'preceding {}'.format(self.per_spec.previous_blank_runid)),
                                         ('icfactors', 'ICFactor', 'default')):
                        p = self._make_path(pp)
                        if os.path.isfile(p):
                            ar.add(p, commit=False)
                            ar.commit('<{}> {}'.format(tag, msg))

                    # push changes
                    dvc.push_repository(ar)

                    # update meta
                    dvc.meta_pull(accept_our=True)

                    dvc.meta_commit('repo updated for analysis {}'.format(self.per_spec.run_spec.runid))

                    # push commit
                    dvc.meta_push()
                except GitCommandError, e:
                    self.warning(e)
                    if self.confirmation_dialog('NON FATAL\n\n'
                                                'DVC/Git upload of analysis not successful.'
                                                'Do you want to CANCEL the experiment?\n',
                                                timeout_ret=False,
                                                timeout=30):
                        ret = False

        with dvc.session_ctx():
            self._save_analysis_db(timestamp)
        self.debug('================= post measurement finished')
        return ret

    def save_run_log_file(self, path):
        if self.save_enabled:
            self.debug('saving run log file')

            npath = self._make_path('logs', '.log')
            shutil.copyfile(path, npath)
            ar = self.active_repository
            ar.smart_pull(accept_their=True)
            ar.add(npath, commit=False)
            ar.commit('<COLLECTION> log')
            self.dvc.push_repository(ar)

    # private
    def _check_repository_identifier(self):
        repo_id = self.per_spec.run_spec.repository_identifier
        db = self.dvc.db
        repo = db.get_repository(repo_id)
        if repo is None:
            self.warning('No repository named ="{}" changing to NoRepo'.format(repo_id))
            self.per_spec.run_spec.repository_identifier = 'NoRepo'
            repo = db.get_repository('NoRepo')
            if repo is None:
                db.add_repository('NoRepo', self.default_principal_investigator)

    def _save_analysis_db(self, timestamp):
        rs = self.per_spec.run_spec
        d = {k: getattr(rs, k) for k in ('uuid', 'analysis_type', 'aliquot',
                                         'increment', 'mass_spectrometer', 'weight', 'comment',
                                         'cleanup', 'duration', 'extract_value', 'extract_units')}

        ed = self.per_spec.run_spec.extract_device
        if ed in (None, '', NULL_STR, LINE_STR, 'Extract Device'):
            d['extract_device'] = 'No Extract Device'
        else:
            d['extract_device'] = ed

        d['timestamp'] = timestamp

        # save script names
        d['measurementName'] = self.per_spec.measurement_name
        d['extractionName'] = self.per_spec.extraction_name

        db = self.dvc.db
        an = db.add_analysis(**d)

        # save media
        if self.per_spec.snapshots:
            for p in self.per_spec.snapshots:
                db.add_media(p, an)

        if self.per_spec.videos:
            for p in self.per_spec.videos:
                db.add_media(p, an)

        if self._positions:
            db = self.dvc.db
            load_name = self.per_spec.load_name

            for position in self._positions:
                pos = db.add_measured_position(load=load_name, **position)
                an.measured_position = pos
        # all associations are handled by the ExperimentExecutor._retroactive_experiment_identifiers
        # *** _retroactive_experiment_identifiers is currently disabled ***

        if self.per_spec.use_repository_association:
            db.add_repository_association(rs.repository_identifier, an)

        self.debug('get identifier "{}"'.format(rs.identifier))
        pos = db.get_identifier(rs.identifier)
        self.debug('setting analysis irradiation position={}'.format(pos))
        an.irradiation_position = pos

        t = self.per_spec.tag

        db.flush()

        change = db.add_analysis_change(tag=t)
        an.change = change

        db.commit()

    def _save_analysis(self, timestamp):

        isos = {}
        dets = {}
        signals = []
        baselines = []
        sniffs = []
        blanks = {}
        intercepts = {}
        cbaselines = {}
        icfactors = {}

        endianness = '>'
        per_spec = self.per_spec

        source = {'emission': per_spec.emission,
                  'trap': per_spec.trap}
        keys = []

        clf = None
        if self.use_isotope_classifier:
            clf = self.application.get_service('pychron.classifier.isotope_classifier.IsotopeClassifier')

        for iso in per_spec.isotope_group.isotopes.values():

            sblob = base64.b64encode(iso.pack(endianness, as_hex=False))
            snblob = base64.b64encode(iso.sniff.pack(endianness, as_hex=False))
            for ss, blob in ((signals, sblob), (sniffs, snblob)):
                d = {'isotope': iso.name, 'detector': iso.detector, 'blob': blob}
                ss.append(d)
                # signals.append({'isotope': iso.name, 'detector': iso.detector, 'blob': sblob})
                # sniffs.append({'isotope': iso.name, 'detector': iso.detector, 'blob': snblob})

            isod = {'detector': iso.detector,
                    'name': iso.name}

            if clf is not None:
                klass, prob = clf.predict_isotope(iso)
                isod.update(classification=klass,
                            classification_probability=prob)
            key = iso.name
            if key in keys:
                if key in isos:
                    nd = isos.pop(key)
                    nkey = '{}{}'.format(nd['name'], nd['detector'])
                    isos[nkey] = nd

                    nd = intercepts.pop(key)
                    intercepts[nkey] = nd

                    nd = blanks.pop(key)
                    blanks[nkey] = nd

                key = '{}{}'.format(key, iso.detector)

            isos[key] = isod

            if iso.detector not in dets:
                bblob = base64.b64encode(iso.baseline.pack(endianness, as_hex=False))
                baselines.append({'detector': iso.detector, 'blob': bblob})
                dets[iso.detector] = {'deflection': per_spec.defl_dict.get(iso.detector),
                                      'gain': per_spec.gains.get(iso.detector)}

                icfactors[iso.detector] = {'value': float(nominal_value(iso.ic_factor or 1)),
                                           'error': float(std_dev(iso.ic_factor or 0)),
                                           'fit': 'default',
                                           'references': []}
                cbaselines[iso.detector] = {'fit': iso.baseline.fit,
                                            'filter_outliers_dict': iso.baseline.filter_outliers_dict,
                                            'value': float(iso.baseline.value),
                                            'error': float(iso.baseline.error)}

            intercepts[key] = {'fit': iso.fit,
                               'filter_outliers_dict': iso.filter_outliers_dict,
                               'value': float(iso.value),
                               'error': float(iso.error)}

            blanks[key] = {'fit': 'previous',
                           'references': [{'record_id': per_spec.previous_blank_runid,
                                           'exclude': False}],
                           'value': float(iso.blank.value),
                           'error': float(iso.blank.error)}

            keys.append(iso.name)

        obj = self._make_analysis_dict()

        # from pychron.version import __version__ as pversion
        # from pychron.experiment import __version__ as eversion
        # from pychron.dvc import __version__ as dversion

        obj['timestamp'] = timestamp.isoformat()

        # obj['collection_version'] = '{}:{}'.format(eversion, dversion)
        # obj['acquisition_software'] = 'pychron version={}'.format(pversion)
        # obj['data_reduction_software'] = 'pychron version={}'.format(pversion)

        obj['environmental'] = {'lab_temperatures': per_spec.lab_temperatures,
                                'lab_humiditys': per_spec.lab_humiditys,
                                'lab_pneumatics': per_spec.lab_pneumatics}

        obj['laboratory'] = per_spec.run_spec.laboratory
        obj['analyst_name'] = per_spec.run_spec.username
        obj['whiff_result'] = per_spec.whiff_result
        obj['detectors'] = dets
        obj['isotopes'] = isos
        obj['spec_sha'] = self._get_spectrometer_sha()
        obj['intensity_scalar'] = per_spec.intensity_scalar
        obj['source'] = source
        # save the conditionals
        obj['conditionals'] = [c.to_dict() for c in per_spec.conditionals] if \
            per_spec.conditionals else None
        obj['tripped_conditional'] = per_spec.tripped_conditional.result_dict() if \
            per_spec.tripped_conditional else None

        # save the scripts
        ms = per_spec.run_spec.mass_spectrometer
        for si in ('measurement', 'extraction', 'post_measurement', 'post_equilibration'):
            name = getattr(per_spec, '{}_name'.format(si))
            blob = getattr(per_spec, '{}_blob'.format(si))
            self.dvc.meta_repo.update_script(ms, name, blob)
            obj[si] = name

        # save experiment
        self.debug('---------------- Experiment Queue saving disabled')
        # self.dvc.update_experiment_queue(ms, self.per_spec.experiment_queue_name,
        #                                  self.per_spec.experiment_queue_blob)

        hexsha = str(self.dvc.get_meta_head())
        obj['commit'] = hexsha

        # dump runid.json
        p = self._make_path()
        dvc_dump(obj, p)

        p = self._make_path(modifier='intercepts')
        dvc_dump(intercepts, p)

        # dump runid.blank.json
        p = self._make_path(modifier='blanks')
        dvc_dump(blanks, p)

        p = self._make_path(modifier='baselines')
        dvc_dump(cbaselines, p)

        p = self._make_path(modifier='icfactors')
        dvc_dump(icfactors, p)

        # dump runid.data.json
        p = self._make_path(modifier='.data')
        data = {'commit': hexsha,
                'encoding': 'base64',
                'format': '{}ff'.format(endianness),
                'signals': signals, 'baselines': baselines, 'sniffs': sniffs}
        dvc_dump(data, p)

    def _save_monitor(self):
        if self.per_spec.monitor:
            p = self._make_path(modifier='monitor')
            checks = []
            for ci in self.per_spec.monitor.checks:
                data = ''.join([struct.pack('>ff', x, y) for x, y in ci.data])
                params = dict(name=ci.name,
                              parameter=ci.parameter, criterion=ci.criterion,
                              comparator=ci.comparator, tripped=ci.tripped,
                              data=data)
                checks.append(params)

            dvc_dump(checks, p)

    def _save_spectrometer_file(self, path):
        obj = dict(spectrometer=dict(self.per_spec.spec_dict),
                   gains=dict(self.per_spec.gains),
                   deflections=dict(self.per_spec.defl_dict))
        # hexsha = self.dvc.get_meta_head()
        # obj['commit'] = str(hexsha)

        dvc_dump(obj, path)

    def _save_peak_center(self, pc):
        self.info('DVC saving peakcenter')
        p = self._make_path(modifier='peakcenter')

        obj = {}
        if pc:
            obj['reference_detector'] = pc.reference_detector.name
            obj['reference_isotope'] = pc.reference_isotope
            fmt = '>ff'
            obj['fmt'] = fmt
            results = pc.get_results()
            if results:
                for result in results:
                    obj[result.detector] = {'low_dac': result.low_dac,
                                            'center_dac': result.center_dac,
                                            'high_dac': result.high_dac,
                                            'low_signal': result.low_signal,
                                            'center_signal': result.center_signal,
                                            'high_signal': result.high_signal,
                                            'points': base64.b64encode(''.join([struct.pack(fmt, *di)
                                                                                for di in result.points]))}

                    # if pc.result:
                    #     xs, ys, _mx, _my = pc.result
                    #     obj.update({'low_dac': xs[0],
                    #                 'center_dac': xs[1],
                    #                 'high_dac': xs[2],
                    #                 'low_signal': ys[0],
                    #                 'center_signal': ys[1],
                    #                 'high_signal': ys[2]})
                    #
                    # data = pc.get_data()
                    # if data:
                    #     fmt = '>ff'
                    #     obj['fmt'] = fmt
                    #     for det, pts in data:
                    #         obj[det] = base64.b64encode(''.join([struct.pack(fmt, *di) for di in pts]))

        dvc_dump(obj, p)

    def _make_path(self, modifier=None, extension='.json'):
        runid = self.per_spec.run_spec.runid
        repository_identifier = self.per_spec.run_spec.repository_identifier
        return analysis_path(runid, repository_identifier, modifier, extension, mode='w')

    def _make_analysis_dict(self, keys=None):
        rs = self.per_spec.run_spec
        if keys is None:
            keys = META_ATTRS

        d = {k: getattr(rs, k) for k in keys}
        return d

    def _get_spectrometer_sha(self):
        """
        return a sha-1 hash.

        generate using spec_dict, defl_dict, and gains
        spec_dict: source parameters, cdd operating voltage
        defl_dict: detector deflections
        gains: detector gains

        make hash using
        for key,value in dictionary:
            sha1.update(key)
            sha1.update(value)

        to ensure consistence, dictionaries are sorted by key
        for key,value in sorted(dictionary)
        :return:
        """
        return spectrometer_sha(self.per_spec.spec_dict, self.per_spec.defl_dict, self.per_spec.gains)

        # ============= EOF =============================================
        #         self._save_measured_positions()
        #
        #
        # def _save_measured_positions(self):
        #     dvc = self.dvc
        #
        #     load_name = self.per_spec.load_name
        #     for i, pp in enumerate(self.per_spec.positions):
        #         if isinstance(pp, tuple):
        #             if len(pp) > 1:
        #                 if len(pp) == 3:
        #                     dvc.add_measured_position('', load_name, x=pp[0], y=pp[1], z=pp[2])
        #                 else:
        #                     dvc.add_measured_position('', load_name, x=pp[0], y=pp[1])
        #             else:
        #                 dvc.add_measured_position(pp[0], load_name)
        #
        #         else:
        #             dbpos = dvc.add_measured_position(pp, load_name)
        #             try:
        #                 ep = self.per_spec.extraction_positions[i]
        #                 dbpos.x = ep[0]
        #                 dbpos.y = ep[1]
        #                 if len(ep) == 3:
        #                     dbpos.z = ep[2]
        #             except IndexError:
        #                 self.debug('no extraction position for {}'.format(pp))
