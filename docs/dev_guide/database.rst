Database
==============

.. code-block:: sql

   update analysestable
   set aliquot_pychron = CAST(analysestable.aliquot as SIGNED INTEGER)
   where `IrradPosition` in #(LIST OF LABNUMBERS)

.. code-block:: sql

   delimiter $$
   CREATE TRIGGER update_aliquot_pychron
   BEFORE INSERT ON analysestable
   FOR EACH ROW BEGIN
   SET NEW.aliquot_pychron = CAST(NEW.aliquot as SIGNED INTEGER);
   END$$
   delimiter ;



Install
--------------------------------------------------

Installing a Mass Spec-compatible MySQL database

:Author: Rich Esser
:Date: 9/27/07

:Updated: Jake Ross
:Date: 4/4/13

#.  Download the MySQL package installer.  As of mid September 2007, it is located at:

    http://dev.mysql.com/get/Downloads/MySQL-5.0/mysql-5.0.45-osx10.4-i686.dmg/from/
    http://mirror.services.wisc.edu/mysql/

    But as time goes by and new versions come out, the above link may no longer
    work.  Going to the general MySQL download site, you will be able to find a
    recent version for the computer in question (you must know if you're installing
    MySQL on a PowerPC (PPC) Mac or Intel Mac and download that particular version):
    http://dev.mysql.com/downloads/.  Open up the disk image that the installer
    arrives in.  Inside you will find and install the " mysql-5.X.XX-osxXXX.pkg"
    (the actual MySQL database application), the "MySQLStartupitem.pkg" (a small
    application that will automatically launch the MySQL program when the computer
    is restarted) and the "MySQL.prefPane" (a System Preferences pane to easily
    turn MySQL on/off).  Double-click and install in the order above (you'll need to
    enter your admin password for most of these installers).  Once all is installed,
    open the 'MySQL' preference pane (in System Preferences) and start the MySQL
    Server and click the checkbox to automatically start MySQL on reboot.  At this
    point, you should probably restart the computer.

#.  To verify the success of the installation, issue the command
    ::

        /usr/local/mysql/bin/mysql --version


    in the Terminal.  The result should be something like

    ::

        /usr/local/mysql/bin/mysql  Ver 14.12 Distrib 5.0.45, for apple-darwin8.5.1 (i686) using readline 5.0

    If you don't get this similar return back, open the MySQL preference pane and make sure that
    MySQL is running ("running" in green text).  If the MySQL server is running, you can now give the
    server a root password.  The root password for MySQL is independent of the MacOS
    admin or root passwords.  In the Terminal, issue the following command:

    ::

        sudo /usr/local/mysql/bin/mysqladmin -u root password "Argon"

    where "Argon" (include the quotes in the Terminal command) is the password to access the
    database.  However, you can make the password whatever you like.  Remember,
    because you issue the command with the sudo, you must enter your Mac admin
    password to get the command to work.

#.  With the root password set, you can now log into the MySQL database with
    client software ( e.g. Sequel Pro).  Using Sequel Pro or another MySQL editor,
    log into the new database (host=localhost, user=root, password=Argon).  In the
    "Choose database..." popup list on the left side of the resulting window, select
    the 'mysql' database.  Go to the bottom of the table list and click on 'user'.
    In the upper-right window, switch from the "Structure" tab to the "Content" tab.
    Highlight the row that has 'localhost' and 'root" (there is probably only 1,
    maybe 2 rows in the table).  Duplicate the highlighted row by clicking the
    'Duplicate' icon at the bottom of the window.  In the resulting row, change the
    'root' to 'massspec' (double-click the 'root' name to edit).  Enter to take the
    change.  Click on the "Flush Privileges" icon at the top of the Sequel Pro
    window.

#.  The Mass Spec program (specifically, RealBasic) uses an older style of
    password/database hashing (look it up, if you're curious), so you must tell the
    newly installed database server to use this older style hashing.  If you skip
    this step, the Mass Spec program will not be able to use the database.  In the
    Terminal, log into the MySQL database:

    ::

        sudo /usr/local/mysql/bin/mysql -u root -p

    Once again, the first password is your MacOS admin password, followed by
    the MySQL root password (Argon).  You should now see the mysql prompt (mysql>).
    Type

    ::

        use mysql;

    with the semi-colon closing the command (all commands typed into the MySQL command line editor
    must be closed/ended by the semi-colon).  Hit return.
    ::

        Database changed

    Next command:

    ::

        UPDATE user SET Password = OLD_PASSWORD('Argon') WHERE Host = 'localhost' AND
        User = 'root';

    ::

        "Query OK, 1 rows affected...".

    Follow it by:
    ::

        UPDATE user SET Password = OLD_PASSWORD('Argon') WHERE Host = 'localhost' AND
        User = 'massspec';

    ::

        Another "Query OK, 1 rows affected...".

    And once again, flush the privileges, either with this command ( flush
    privileges;) or with Sequel Pro.

    That should do it.  You're now ready to import a 'massspecdata' database using the normal procedures.
    Remember to first create the database (using CocoaMySQL) that you're going to import in to.  Then import:

    ::

        sudo /usr/local/mysql/bin/mysql -u root -p massspecdata < the_backed_up_database_location_and_name

    The above are bare-bones instructions for getting MySQL up and running for a local-only system.  In other words, no one from outside
    the computer you just installed MySQL on can access this database server.  If this is desired, there are several additional steps needed.


Replication
-------------------

Setup a MySQL replication server

:Author: Alan Deino
:Date: 2/2011
:Source: Mass Spec Manual Version 7.849

:Modified: Jake Ross
:Date: 4/4/2013

A significant improvement over the single MySQL server approach is to set up a replication MySQL server
on a separate computer, which will automatically mirror the database on the main (‘master’) server.
Any changes that occur in the master, like storage of new analytical data, are immediately updated in the replication server,
or ‘slave.’ You can do the periodic (e.g., nightly) database dumps on the slave, so that the master doesn’t get
bogged down and potentially drastically slow the mass spectrometer data collection operation during the period of
the backup. Also, the intention is in the future to have Mass Spec detect failure of the master server,
and automatically continue operation with the slave. This is not yet implemented as of 7.782.

To set up a replication server, you could do the following:

#.  Stop all data collection and reduction operations.
#.  Create a dump of the MassSpecData database on the master MySQL server.
#.  Create a new MySQL server on the replication computer. Note that the best approach is to also
    update the master server so that the two MySQL versions are the same.
#.  Set up the slave MySQL account in the same way as the master
    (see the User table in the MySQL database; remember to Flush Priviledges after changing the User account).
#.  Load the data backup from step #2 into the slave MySQL in the manner indicated in the previous section.
#.  You now have two identical MySQL instances. One must be designated the master and the other the slave through
    the use of configuration files (‘my.cnf), read by the instances on startup.
#.  Master my.cnf: Edit or create the my.cnf file in the MySQL data folder, located usually at /usr/local/mysql/data.
    You can also find or create it in /etc. Add to this file:

    ::

        [mysqld]
        log-bin
        binlog-do-db=massspecdata
        server-id=1

#.  Stop the master server (typically using the MySQL preference pane in the System Preferences window).
#.  Restart the master server.
#.  From the terminal command line, on in Sequel Pro or YourSQL, issue the following SQL command:

    ::

        SHOW MASTER STATUS


    The response should be a file name, position, and the name of the database being logged.

#.  Slave my.cnf: Edit or create the my.cnf file in the MySQL data folder, located usually at /usr/local/mysql/data.
    You can also find or create it in /etc. Add to this file (replace italicized fields with your appropriate data):

    ::

        [mysqld]
        server-id=2
        master-host= put the IP address of the master here master-user=massspec
        master-password=the Mass Spec database access password master-connect-retry=60
        replicate-do-db=massspecdata

#.  If you place your .cnf files in /etc, make sure the owner/group is mysql, with the following commands issued in a terminal window:

    ::

        sudo chown mysql:mysql /etc/my.cnf
        sudo chmod 770 /etc/my.cnf

#.  Stop/start the slave MySQL instance.
#.  Issue the following SQL command:

    ::

        STOP SLAVE

#.  Issue the following SQL command:

    ::

        CHANGE MASTER TO master_host='MH',master_user='MU',master_password='MP', master_log_file='MLF',master_log_pos=MLP


    where MH= ``IP address of master``, MU= ``master username e.g massspec``, MP= ``the Mass Spec database access password``, MLF= ``the file name obtained in step #10`` and MLP= ``the postion obtained in step #10``

#.  Issue the following SQL command:

    ::

        START SLAVE


    The replication server should now be operational. Test it by making a small change in the master database; this change should be reflected in the slave database.

