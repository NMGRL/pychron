#required to fix atexit bug with travis ci
import multiprocessing

#prevent pycharm from remove multiprocessing during import optimization
multiprocessing

from setuptools import setup

setup(name='pychron',
      version='2.0.4',
      setup_requires=['nose>=1.0'],
      py_modules=['pychron.pychron_constants',
                  'pychron.processing.plateau'],
      packages=['pychron.core.regression',
                'pychron.core.stats',
                'pychron.external_pipette',

                'pychron.core.regression.tests',
                'pychron.processing.tests',
                'pychron.external_pipette.tests'
      ],
      # test_suite='pychron.core.regression.tests.suite'
      test_suite='pychron.test_suite.suite')
