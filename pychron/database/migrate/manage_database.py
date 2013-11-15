import os

from migrate.versioning.api import version_control, upgrade, version
from migrate.exceptions import DatabaseAlreadyControlledError, KnownError, \
    InvalidRepositoryError


def manage_version(url, base_repo):
    repo = os.path.join(os.path.dirname(__file__), base_repo)
    try:
        version_control(url, repo)
    except InvalidRepositoryError:
        from pychron.paths import paths

        repo = os.path.join(paths.app_resources, 'migrate_repositories', base_repo)
        try:
            version_control(url, repo)
        except InvalidRepositoryError:
            pass
        except DatabaseAlreadyControlledError:
            pass

    except DatabaseAlreadyControlledError:
        pass

    return repo


def manage_database(url, repo, logger=None, progress=None):

# 	url = url.format(root)
# 	url = 'sqlite:///{}'.format(name)

    kind, path = url.split('://')
    if logger:
        logger.debug('sadfa {} {}'.format(url, repo))
    if kind == 'sqlite':
        b = os.path.split(path[1:])[0]
        if not os.path.isdir(b):
            os.mkdir(b)

    repo = manage_version(url, repo)
    n = version(repo)

    if progress:
        progress.max = int(n)

    for i in range(n + 1):
        try:
            msg = 'upgrading {} to {}'.format(repo, i)
            upgrade(url, repo, version=i)

        except KnownError:
            msg = 'skipping version {}'.format(i)

        finally:
            if progress:
                progress.change_message(msg)
            if logger:
                logger.info(msg)

    if logger:
        logger.info('Upgrade complete')

# if __name__ == '__main__':
#
# 	root = '/usr/local/pychron'
# 	dbs = [
# #		('{}/co2.sqlite', 'co2laserdb'),
# #		('{}/bakeoutdb/bakeouts.sqlite', 'bakeoutdb'),
# 		('{}/device_scans/device_scans.sqlite', 'device_scans'),
# 		('{}/diode.sqlite', 'diodelaserdb')
# 		]
#
# #	root = '/Users/ross/Sandbox/sqlite'
# #	dbs = [
# #		('{}/co2.sqlite', 'co2laserdb'),
# #		('{}/bakeouts.sqlite', 'bakeoutdb'),
# #		('{}/device_scans.sqlite', 'device_scans'),
# #
# #		]
#
# 	for url, repo in dbs:
# 		url = url.format(root)
#
# 		b = os.path.split(url)[0]
# 		if not os.path.isdir(b):
# 			os.mkdir(b)
# 		url = 'sqlite:///{}'.format(url)
#
# 		print url
# 		try:
# 			version_control(url, repo)
# 		except DatabaseAlreadyControlledError:
# 			pass
#
# #		print version(repo)
# 		n = version(repo)
# 		for i in range(n + 1):
# 			try:
# 				upgrade(url, repo, version=i)
# 				print 'upgrading {} to {}'.format(repo, i)
# 			except KnownError:
# 				pass
# 		#test(url, repo)
# 		#upgrade(url, repo)

