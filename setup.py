from setuptools import setup

setup(name='pychron',
      version='2.0.4',
      setup_requires=['nose>=1.0'],
      py_modules=['pychron_constants'],
      packages=[
          'pychron.core.regression',
                'pychron.core.stats',
                'pychron.core.regression.tests'],
      test_suite='pychron.core.regression.tests.suite')
