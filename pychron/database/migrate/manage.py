#!/usr/bin/env python
from migrate.versioning.shell import main
# from pychron.database.shell import main as pychron_main
if __name__ == '__main__':

#    main(url='sqlite:////usr/local/pychron/isotope.sqlite', debug='False', repository='isotopedb/')


#    p = '/Users/ross/Pychrondata_experiment/data/isotopedb.sqlite'
# p = '/usr/local/pychron/isotope.sqlite
#    p = '/Users/ross/Sandbox/pychron_test_data/data/isotopedb.sqlite'
#    main(url='sqlite:///{}'.format(p) , debug='False', repository='isotopedb/')

#    url = 'mysql://root:Argon@localhost/isotopedb?connect_timeout=3'
    url = 'mysql+pymysql://root:Argon@localhost/isotopedb_dev?connect_timeout=3'
    #url = 'mysql+pymysql://root:Argon@localhost/pychronlocal?connect_timeout=3'
    #url = 'mysql+pymysql://root:Argon@localhost/isotopedb_dev_migrate?connect_timeout=3'
    #    url = 'mysql://root:Argon@localhost/isotopedb_FC2?connect_timeout=3'
    # url = 'mysql://massspec:DBArgon@129.138.12.131/isotopedb_dev_mod?connect_timeout=3'
    #url = 'mysql+pymysql://massspec:DBArgon@129.138.12.160/pychrondata?connect_timeout=3'
    # url = 'mysql+pymysql://massspec:DBArgon@129.138.12.160/pychrondata?connect_timeout=3'
    #    url = 'mysql+pymysql://root:Argon@localhost/pychrondata_minnabluff?connect_timeout=3'

    #     url = 'mysql://root:Argon@localhost/isotopedb_dev?connect_timeout=3'
    main(url=url, debug='False', repository='isotopedb/')

#    url = 'sqlite:////Users/ross/Sandbox/local_lab.db'
# main(url=url , debug='False', repository='local_labdb/')

#    url = 'mysql://root:Argon@localhost/hardwaredb_dev?connect_timeout=3'
#    main(url=url , debug='False', repository='hardwaredb/')

# url = 'sqlite:////Users/ross/Sandbox/bakeout.db'
# url = 'sqlite:////usr/local/pychron/bakeoutdb/bakeouts.sqlite'
#    main(url=url , debug='False', repository='bakeoutdb/')
#    url = 'sqlite:////Users/ross/Sandbox/powermap.db'
#    main(url=url , debug='False', repository='powermapdb/')



#    pychron_main()
