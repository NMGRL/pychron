~/.edm/envs/edm/bin/flake8 . --extend-exclude=docs/,zobs/,sandbox/,test/,alembic_dvc --count --exit-zero \
  --max-complexity=10 --max-line-length=127 --statistics --ignore E501