from traits.etsconfig.etsconfig import ETSConfig

ETSConfig.toolkit = 'qt4'

#required to fix atexit bug with travis ci
import multiprocessing

#prevent pycharm from remove multiprocessing during import optimization
multiprocessing
from setuptools import setup

setup(name='pychron',
      version='2.0.4',
      setup_requires=['nose>=1.0'],
      py_modules=['pychron.pychron_constants',
                  'pychron.processing.plateau',
                  'pychron.processing.ratio',
                  'pychron.core.ui.__init__',
                  'pychron.experiment.utilities.position_regex',
                  'pychron.experiment.utilities.frequency_generator',
                  'pychron.experiment.utilities.aliquot_numbering',
                  'pychron.entry.loaders.analysis_loader'],
      package_data={'pychron.pyscripts.tests': ['data/*.yaml', 'data/*.py'],
                    'pychron.entry.tests': ['data/*.xls']},
      packages=['pychron.core.regression',
                'pychron.core.stats',
                'pychron.external_pipette',
                'pychron.pyscripts',

                #test packages
                'pychron.core.regression.tests',
                'pychron.processing.tests',
                'pychron.external_pipette.tests',
                'pychron.experiment.tests',
                'pychron.pyscripts.tests',
                'pychron.entry.tests'],
      test_suite='pychron.test_suite.suite')
