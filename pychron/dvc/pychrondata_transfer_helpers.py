# ===============================================================================
# Copyright 2016 Jake Ross
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
import json
import os
from datetime import timedelta
from itertools import groupby

from numpy import array, array_split

from pychron.core.helpers.datetime_tools import bin_timestamps, make_timef, get_datetime
from pychron.database.isotope_database_manager import IsotopeDatabaseManager
from pychron.dvc import dvc_dump, dvc_load
from pychron.dvc.dvc_analysis import analysis_path
from pychron.dvc.dvc_persister import spectrometer_sha
from pychron.github import Organization
from pychron.pychron_constants import QTEGRA_SOURCE_KEYS

"""
http://stackoverflow.com/questions/6944165/mysql-update-with-where-select-subquery-error

update gen_sampletable
set project_id =209
where id in
(select id from (select id from gen_sampletable where
gen_sampletable.name like "NMVC-%" or
gen_sampletable.name like "NMRC-%" or
gen_sampletable.name like "JS-94-48%" or
gen_sampletable.name like "NMZB-%" or
gen_sampletable.name like "NMVF-%" or
gen_sampletable.name like "NMAV-%" or
gen_sampletable.name like "NMPV-%" or
gen_sampletable.name like "NMRQ-%" or
gen_sampletable.name like "Bardarbunga-1%" or
gen_sampletable.name like "NM-MAS-%" or
gen_sampletable.name like "NMBC-%" or
gen_sampletable.name like "AV-41%" or
gen_sampletable.name like "AV-58%" or
gen_sampletable.name like "AV-59%" or
gen_sampletable.name like "DL-J15-7%" or
gen_sampletable.name like "NMJV-%" or
gen_sampletable.name like "NMLC-%" or
gen_sampletable.name like "NMCH-%" or
gen_sampletable.name like "NMGS-%") as t1)
"""


def import_j(src, dest, meta, repo_identifier):
    # idns = {ra.analysis.irradiation_position.identifier
    #             for ra in repo.repository_associations}

    idns = []
    with dest.session_ctx():
        repo = dest.get_repository(repo_identifier)
        decay = {'lambda_k_total': 5.543e-10,
                 'lambda_k_total_error': 9.436630754670864e-13}

        with src.session_ctx():

            for ra in repo.repository_associations:
                ip = ra.analysis.irradiation_position
                idn = ip.identifier
                if idn not in idns:
                    idns.append(idn)
                    irradname = ip.level.irradiation.name
                    levelname = ip.level.name
                    pos = ip.position
                    # print idn, irradname, levelname, pos

                    sip = src.get_irradiation_position(irradname, levelname, pos)
                    if sip is not None:
                        fhs = sip.flux_histories
                        if fhs:
                            fh = fhs[-1]
                            flux = fh.flux
                            j, e = flux.j, flux.j_err
                            meta.update_flux(irradname, levelname, pos, idn, j, e, decay, [], add=False)
                    else:
                        print 'no irradiation position {} {} {} {}'.format(idn, irradname, levelname, pos)







def fix_import_commit(repo_identifier, root):
    from pychron.git_archive.repo_manager import GitRepoManager
    rm = GitRepoManager()
    proot = os.path.join(root, repo_identifier)
    rm.open_repo(proot)

    repo = rm._repo
    print '========= {} ======'.format(repo_identifier)
    txt = repo.git.log('--pretty=oneline')
    print txt
    # first_commit = txt.split('\n')[0]
    # # print first_commit, 'initial import' in first_commit
    # if 'initial import' in first_commit:
    #     print 'amend'
    #     repo.git.commit('--amend', '-m', '<Import> initial')
    #     repo.git.push('--force')


def fix_meta(dest, repo_identifier, root):
    d = os.path.join(root, repo_identifier)
    changed = False
    with dest.session_ctx():
        repo = dest.get_repository(repo_identifier)
        for ra in repo.repository_associations:
            an = ra.analysis
            p = analysis_path(an.record_id, repo_identifier)
            obj = dvc_load(p)
            if not obj:
                print '********************** {} not found in repo'.format(an.record_id)
                continue

            print an.record_id, p
            if not obj['irradiation']:
                obj['irradiation'] = an.irradiation
                lchanged = True
                changed = True
            if not obj['irradiation_position']:
                obj['irradiation_position'] = an.irradiation_position_position
                lchanged = True
                changed = True
            if not obj['irradiation_level']:
                obj['irradiation_level'] = an.irradiation_level
                lchanged = True
                changed = True
            if not obj['material']:
                obj['material'] = an.irradiation_position.sample.material.name
                lchanged = True
                changed = True
            if not obj['project']:
                obj['project'] = an.irradiation_position.sample.project.name
                lchanged = True
                changed = True

            if obj['repository_identifier'] != an.repository_identifier:
                obj['repository_identifier'] = an.repository_identifier
                lchanged = True
                changed = True

            if lchanged:
                print '{} changed'.format(an.record_id)
                dvc_dump(obj, p)

    if changed:
        from pychron.git_archive.repo_manager import GitRepoManager
        rm = GitRepoManager()
        rm.open_repo(d)

        repo = rm._repo
        repo.git.add('.')
        repo.git.commit('-m', '<MANUAL> fixed metadata')
        repo.git.push()


def fix_a_steps(dest, repo_identifier, root):
    with dest.session_ctx():
        repo = dest.get_repository(repo_identifier)

        ans = [(ra.analysis.irradiation_position.identifier, ra.analysis.aliquot, ra.analysis.increment,
                ra.analysis.record_id, ra.analysis.id)
               for ra in repo.repository_associations]
        key = lambda x: x[0]
        ans = sorted(ans, key=key)
        for identifier, ais in groupby(ans, key=key):
            try:
                int(identifier)
            except ValueError:
                continue

            # groupby aliquot
            key = lambda xi: xi[1]
            for aliquot, ais in groupby(ais, key=key):
                ais = sorted(ais, key=lambda ai: ai[2])
                print identifier, aliquot, ais
                # if the first increment for a given aliquot is 1
                # and the increment for the first analysis of the aliquot is None
                if len(ais) == 1:
                    continue

                if ais[0][2] is None and ais[1][2] == 1:
                    an = dest.get_analysis(ais[0][4])
                    print 'fix', ais[0], an, an.record_id
                    original_record_id = str(an.record_id)
                    path = analysis_path(an.record_id, repo_identifier)
                    obj = dvc_load(path)
                    obj['increment'] = 0

                    an.increment = 0
                    npath = analysis_path(an.record_id, repo_identifier)
                    dvc_dump(obj, npath)
                    os.remove(path)

                    for modifier in ('baselines', 'blanks', 'extraction',
                                     'intercepts', 'icfactors', 'peakcenter', '.data'):
                        npath = analysis_path(an.record_id, repo_identifier, modifier=modifier)
                        opath = analysis_path(original_record_id, repo_identifier, modifier=modifier)
                        # print opath, npath
                        os.rename(opath, npath)


def commit_initial_import(repo_identifier, root):
    from pychron.git_archive.repo_manager import GitRepoManager
    rm = GitRepoManager()
    proot = os.path.join(root, repo_identifier)
    rm.open_repo(proot)

    repo = rm._repo
    repo.git.add('.')
    repo.git.commit('-m', '<IMPORT> initial')
    repo.git.push('--set-upstream', 'origin', 'master')


def create_repo_for_existing_local(repo_identifier, root, organization='NMGRLData'):
    from pychron.git_archive.repo_manager import GitRepoManager
    repo = GitRepoManager()
    proot = os.path.join(root, repo_identifier)
    repo.open_repo(proot)

    org = Organization(organization)
    if not org.has_repo(repo_identifier):
        usr = os.environ.get('GITHUB_USER')
        pwd = os.environ.get('GITHUB_PASSWORD')
        org.create_repo(repo_identifier, usr, pwd)
        url = 'https://github.com/{}/{}.git'.format(organization, repo_identifier)
        repo.create_remote(url)


def set_spectrometer_files(src, dest, repo_identifier, root):
    """

    @param src: pychrondata style database
    @param dest: pychrondvc style database
    @param repo_identifier:
    @param root: path to repository root
    @return:
    """

    # get all analyses associated with repo_identifier
    with dest.session_ctx():
        dbrepo = dest.get_repository(repo_identifier)
        analyses = [ra.analysis.uuid for ra in dbrepo.repository_associations]

    # get analyses from src database
    with src.session_ctx():
        for an in analyses:
            dban = src.get_analysis_uuid(an)
            print 'set spectrometer file for {}'.format(dban.record_id)
            set_spectrometer_file(dban, root)


def set_spectrometer_file(dban, root):
    meas = dban.measurement
    gain_history = dban.gain_history
    gains = {}
    if gain_history:
        gains = {d.detector.name: d.value for d in gain_history.gains if d.value is not None}

    # deflections
    deflections = {d.detector.name: d.deflection for d in meas.deflections if d.deflection is not None}

    # source
    src = {k: getattr(meas.spectrometer_parameters, k) for k in QTEGRA_SOURCE_KEYS}

    obj = dict(spectrometer=src,
               gains=gains,
               deflections=deflections)
    # hexsha = self.dvc.get_meta_head()
    # obj['commit'] = str(hexsha)
    spec_sha = spectrometer_sha(src, gains, deflections)
    path = os.path.join(root, '{}.json'.format(spec_sha))
    dvc_dump(obj, path)

    # update analysis's spec_sha
    path = analysis_path(dban.record_id, os.path.basename(root))
    obj = dvc_load(path)
    obj['spec_sha'] = spec_sha
    dvc_dump(obj, path)


def get_project_bins(project):
    # src = self.processor.db
    src = IsotopeDatabaseManager(dict(host='localhost',
                                      username=os.environ.get('LOCALHOST_DB_USER'),
                                      password=os.environ.get('LOCALHOST_DB_PWD'),
                                      kind='mysql',
                                      # echo=True,
                                      name='pychrondata'))
    tol_hrs = 6
    # self.debug('bulk import project={}, pi={}'.format(project, principal_investigator))
    ts, idxs = get_project_timestamps(src.db, project, tol_hrs=tol_hrs)

    # repository_identifier = project
    # def filterfunc(x):
    #     a = x.labnumber.irradiation_position is None
    #     b = False
    #     if not a:
    #         b = x.labnumber.irradiation_position.level.irradiation.name == irradname
    #
    #     d = False
    #     if x.extraction:
    #         ed = x.extraction.extraction_device
    #         if not ed:
    #             d = True
    #         else:
    #             d = ed.name == 'Fusions CO2'
    #
    #     return (a or b) and d
    #
    for ms in ('jan', 'obama'):
        for i, ais in enumerate(array_split(ts, idxs + 1)):
            if not ais.shape[0]:
                continue

            low = get_datetime(ais[0]) - timedelta(hours=tol_hrs / 2.)
            high = get_datetime(ais[-1]) + timedelta(hours=tol_hrs / 2.)

            print ms, low, high


def get_project_timestamps(src, project, mass_spectrometer, tol_hrs):
    sql = """SELECT ant.analysis_timestamp from meas_AnalysisTable as ant
join gen_LabTable as lt on lt.id = ant.lab_id
join gen_SampleTable as st on lt.sample_id = st.id
join gen_ProjectTable as pt on st.project_id = pt.id
join meas_MeasurementTable as mst on ant.measurement_id = mst.id
join gen_MassSpectrometerTable as ms on mst.mass_spectrometer_id = ms.id
where pt.name="{}" and ms.name="{}"
order by ant.analysis_timestamp ASC
""".format(project, mass_spectrometer)

    return get_timestamps(src, sql, tol_hrs)


def get_irradiation_timestamps(src, irradname, tol_hrs):
    sql = """SELECT ant.analysis_timestamp from meas_AnalysisTable as ant
    join gen_LabTable as lt on lt.id = ant.lab_id
    join gen_SampleTable as st on lt.sample_id = st.id
    join irrad_PositionTable as irp on lt.irradiation_id = irp.id
    join irrad_LevelTable as il on irp.level_id = il.id
    join irrad_IrradiationTable as ir on il.irradiation_id = ir.id

    where ir.name = "{}" and st.name ="FC-2"
    order by ant.analysis_timestamp ASC

    """.format(irradname)

    return get_timestamps(src, sql, tol_hrs)


def get_timestamps(src, sql, tol_hrs):
    with src.session_ctx() as sess:
        result = sess.execute(sql)
        ts = array([make_timef(ri[0]) for ri in result.fetchall()])

        idxs = bin_timestamps(ts, tol_hrs=tol_hrs)
        return ts, idxs


def experiment_id_modifier(root, expid):
    for r, ds, fs in os.walk(root, topdown=True):
        fs = [f for f in fs if not f[0] == '.']
        ds[:] = [d for d in ds if not d[0] == '.']

        # print 'fff',r, os.path.basename(r)
        if os.path.basename(r) in ('intercepts', 'blanks', '.git',
                                   'baselines', 'icfactors', 'extraction', 'tags', '.data', 'monitor', 'peakcenter'):
            continue
        # dcnt+=1
        for fi in fs:
            # if not fi.endswith('.py') or fi == '__init__.py':
            #     continue
            # cnt+=1
            p = os.path.join(r, fi)
            # if os.path.basename(os.path.dirname(p)) =
            print p
            write = False
            with open(p, 'r') as rfile:
                jd = json.load(rfile)
                if 'repository_identifier' in jd:
                    jd['repository_identifier'] = expid
                    write = True

            if write:
                dvc_dump(jd, p)


def runlist_load(path):
    with open(path, 'r') as rfile:
        runs = [li.strip() for li in rfile]
        # runs = [line.strip() for line in rfile if line.strip()]
        return filter(None, runs)


def runlist_loads(txt):
    runs = [li.strip() for li in txt.striplines()]
    return filter(None, runs)


def load_path():
    # path = '/Users/ross/Sandbox/dvc_imports/NM-276.txt'
    # expid = 'Irradiation-NM-276'
    # creator = 'mcintosh'

    path = '/Users/ross/Sandbox/dvc_imports/chesner_unknowns.txt'
    expid = 'toba'
    creator = 'root'

    runs = runlist_load(path)
    return runs, expid, creator


def load_import_request():
    import pymysql.cursors
    # Connect to the database
    connection = pymysql.connect(host='localhost',
                                 user=os.environ.get('DB_USER'),
                                 passwd=os.environ.get('DB_PWD'),
                                 db='labspy',
                                 cursorclass=pymysql.cursors.DictCursor)

    try:
        # connection is not autocommit by default. So you must commit to save
        # your changes.
        # connection.commit()

        with connection.cursor() as cursor:
            # Read a single record
            # sql = "SELECT `id`, `password` FROM `users` WHERE `email`=%s"
            # cursor.execute(sql, ('webmaster@python.org',))
            sql = '''SELECT * FROM importer_importrequest'''
            cursor.execute(sql)
            result = cursor.fetchone()

            runs = result['runlist_blob']
            expid = result['repository_identifier']
            creator = result['requestor_name']

            return runs, expid, creator
    finally:
        connection.close()

# ============= EOF =============================================
