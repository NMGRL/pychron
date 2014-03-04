from setuptools import setup

setup(name='pychron',
      version='2.0.4',
      packages=['pychron.core.regression',
                'pychron.core.regression.tests'],
      test_suite='pychron.core.regression.tests.suite'
)