# from traits.etsconfig.etsconfig import ETSConfig

# ETSConfig.toolkit = 'qt4'

# required to fix atexit bug with travis ci
# import multiprocessing
# prevent pycharm from remove multiprocessing during import optimization
# multiprocessing

import os

from setuptools import setup

os.environ['TRAVIS_CI'] = 'True'

setup(name='pychron',
      version='2.4',
      setup_requires=['nose>=1.0'],
      py_modules=['pychron.pychron_constants',
                  'pychron.paths',
                  'pychron.processing.plateau',
                  'pychron.processing.ratio',
                  'pychron.core.ui.__init__',
                  'pychron.core.test_helpers',
                  'pychron.core.filtering',
                  'pychron.core.spell_correct',
                  'pychron.experiment.automated_run.spec',
                  'pychron.experiment.utilities.repository_identifier',
                  'pychron.experiment.utilities.identifier',
                  'pychron.experiment.utilities.position_regex',
                  'pychron.experiment.utilities.frequency_generator',
                  'pychron.experiment.utilities.aliquot_numbering',
                  'pychron.entry.loaders.analysis_loader',
                  'pychron.core.geometry.affine'
                  ],
      package_data={'pychron.pyscripts.tests': ['data/*.yaml', 'data/*.py'],
                    'pychron.entry.tests': ['data/*.xls', 'data/*.db'],
                    'pychron.processing.tests': ['data/*.db'],
                    'pychron.stage.tests': ['data/*.txt']},
      packages=['pychron.core.regression',
                'pychron.core.stats',
                'pychron.core.helpers',
                'pychron.external_pipette',
                'pychron.experiment.conditional',
                'pychron.pyscripts',
                'pychron.stage.maps',

                # test packages
                'pychron.stage.tests',
                'pychron.core.tests',
                'pychron.core.stats.tests',
                'pychron.core.regression.tests',
                'pychron.processing.tests',
                'pychron.external_pipette.tests',
                'pychron.experiment.tests',
                'pychron.pyscripts.tests',
                'pychron.entry.tests'],
      test_suite='pychron.test_suite.suite')

