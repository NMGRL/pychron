.. image:: /images/preferences/update_misc.png

Update
-------

1. Enable Update Plugin using the ``initialization.xml`` file or   ``Menu/Help/Edit Initialization``
2. Restart Pychron
3. Open Pychron's ``Preferences`` and goto the ``Update`` section
4. In the Update Repo section set the "Name" of Pychron fork you will be using.  Each organization typically has its
   own fork.  For example ``NMBGMR/Pychron``.

.. image:: /images/UpdatePreferences.png
    :scale: 70%

5. After setting a valid name, test connection to the fork and load available tags and branches using the "Test
   Connection" button to the right of the "Name" entry field.
6. Set the build directory.  This is the location on your computer where the code actually "lives". If your
   version of Pychron was installed using the installer script your should already have a build directory on
   your computer, typically ``/Users/<username>/.pychron.0/pychron``

7. Set the Branch
8. |bricks| Checkout the Branch
9. |pull| Update the Branch


.. |bricks| image:: /images/preferences/bricks.png
.. |pull| image:: /images/preferences/arrow_down.png
