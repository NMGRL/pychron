# ===============================================================================
# Copyright 2020 ross
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
import os
import uuid

from pychron.core.helpers import logger_setup
from pychron.core.helpers.iterfuncs import groupby_key
from pychron.core.helpers.logger_setup import logging_setup
from pychron.dvc.dvc_persister import DVCPersister, format_repository_identifier
from pychron.entry.legacy.nmgrl.extractor.jadj_extractor import JAdjustmentExtractor
from pychron.entry.legacy.nmgrl.importer.irradiation import IrradiationImporter
from pychron.entry.legacy.nmgrl.importer.sample import SampleImporter
from pychron.entry.legacy.nmgrl.extractor.mass_spec_binary_extractor import MassSpecBinaryExtractor
from pychron.entry.legacy.util import get_dvc
from pychron.experiment.automated_run.persistence_spec import PersistenceSpec
from pychron.experiment.automated_run.spec import AutomatedRunSpec
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.github import Organization
from pychron.paths import paths


def create_github_repo(name):
    pass
    # org = Organization('NMGRLData')
    # if not org.has_repo(name):
    #     usr = os.environ.get('GITHUB_USER')
    #     pwd = os.environ.get('GITHUB_PASSWORD')
    #     org.create_repo(name, usr, pwd)


def add_repository(dvc, repository_identifier, creator, create_repo):
    repository_identifier = format_repository_identifier(repository_identifier)

    # sys.exit()
    proot = os.path.join(paths.repository_dataset_dir, repository_identifier)
    if not os.path.isdir(proot):
        # create new local repo
        os.mkdir(proot)

        repo = GitRepoManager()
        repo.open_repo(proot)

        repo.add_ignore('.DS_Store')
        # self.repo_man = repo
        if create_repo:
            # add repo to central location
            print('create repo not enabled')
            # create_github_repo(repository_identifier)
            # url = 'https://github.com/{}/{}.git'.format(ORG, repository_identifier)
            # print('Create repo at github. url={}'.format(url))
            # repo.create_remote(url)
    else:
        repo = GitRepoManager()
        repo.open_repo(proot)

    dbexp = dvc.db.get_repository(repository_identifier)
    if not dbexp:
        dvc.add_repository(repository_identifier, creator)

    return repo


def run_import(persister, sample_spec, irrad_spec, meta_spec, run):
    if persister.dvc:
        dest = persister.dvc.db

        if dest.get_analysis_runid(run.identifier, run.aliquot, run.step):
            print('run already exists: {}'.format(run.runid))
            # self.warning('{} already exists'.format(make_runid(idn, aliquot, step)))
            return

    rs = AutomatedRunSpec(labnumber=run.identifier,
                          username=meta_spec['username'],
                          material=sample_spec.material.name,
                          project=sample_spec.project.name,
                          sample=sample_spec.name,
                          irradiation=irrad_spec[0],
                          irradiation_level=irrad_spec[1],
                          irradiation_position=irrad_spec[2],
                          repository_identifier=meta_spec['repository_identifier'],
                          mass_spectrometer=meta_spec['mass_spectrometer'],
                          uuid=str(uuid.uuid4()),
                          step=run.step,
                          comment=run.comment,
                          aliquot=int(run.aliquot),
                          extract_device=run.extract_device,
                          duration=run.totdur_heating,
                          extract_value=run.final_set_power,
                          # cleanup=extraction.cleanup_duration,
                          # beam_diameter=extraction.beam_diameter,
                          # extract_units=extraction.extract_units or '',
                          # pattern=extraction.pattern or '',
                          # weight=extraction.weight,
                          # ramp_duration=extraction.ramp_duration or 0,
                          # ramp_rate=extraction.ramp_rate or 0,
                          # queue_conditionals_name='',
                          # tray=''
                          )

    ps = PersistenceSpec(run_spec=rs,
                         tag='ok',
                         isotope_group=run.isotope_group,
                         timestamp=run.timestamp,
                         use_repository_association=True,
                         )
    print('transfer analysis with persister')
    persister.per_spec_save(ps, commit=False, commit_tag='MS Flat File Transfer')


def main():
    p = '../tests/data/MS Data Takahe iso all/MS Data File'
    plt = '../tests/data/MS Data Takahe iso all/MS Lookup Table'

    p = '../tests/data/MS Data NM-115/MS Data File'
    plt = '../tests/data/MS Data NM-115/MS Lookup Table'
    logging_setup('msbinary_importer', root='.')
    ex = MassSpecBinaryExtractor()
    dvc = None
    dvc = get_dvc()
    irradiation_importer = IrradiationImporter(dvc=dvc)
    sample_importer = SampleImporter(dvc=dvc)
    jadj_extractor = JAdjustmentExtractor()
    persister = DVCPersister(dvc=dvc, bind=False, load_mapping=False)
    fails = []
    specs = []
    with open(plt, 'r') as rfile:
        for line in rfile:
            line = line.strip()
            try:
                start, runid = line.split('   ')
            except ValueError:
                start, runid = line.split('  ')

            # print('extracting {}: {}'.format(start, runid))
            try:
                run = ex.extract_analysis(p, int(start), runid)
                if not run:
                    continue
            except BaseException as e:
                print('failure: {}, e={}'.format(line, e))
                # print('failed: e={}'.format(e))
                fails.append(runid)
                continue

                # import traceback
                # traceback.print_exc()
                # break
                # print('failed to extract {}. e={}'.format(runid, e))

            run.startrec = int(start)
            run.runid = runid

            sample_spec = sample_importer.find_spec(run)
            if sample_spec:
                specs.append((sample_spec, run))

    print('total run fails {}'.format(len(fails)))
    for f in fails:
        print('failed run', f)

    if dvc:
        dvc.add_mass_spectrometer('MAP', 'MAP215-50')
    for project, sample_specs in groupby_key(specs, key=lambda s: s[0].project.name):
        if dvc:
            with dvc.session_ctx():
                repo = add_repository(dvc, project, 'NMGRL', True)

                persister.active_repository = repo
                dvc.current_repository = repo

        for sample_spec, run in sample_specs:
            info = sample_importer.fetch_irradiation_info(sample_spec)
            if info is not None:

                # fetch j data
                ln = run.runid.split('-')[0]
                if ln != '50681':
                    break

                j = jadj_extractor.fetch_j(ln)
                if j is not None:
                    dbsam = sample_importer.do_import(sample_spec)
                    irradiation_importer.do_import(dbsam, run, j, *info)
                    meta = {'username': 'BMcIntosh',
                            'mass_spectrometer': 'MAP',
                            'repository_identifier': repo.pathname}
                    dvc.add_extraction_device(run.extract_device)
                    run_import(persister, sample_spec, info, meta, run)

                    # print('breaking for debug')
                    # break
                else:
                    print('no j found for {} in J Adjustment table {}'.format(ln, jadj_extractor.path))

if __name__ == '__main__':
    main()
# ============= EOF =============================================
