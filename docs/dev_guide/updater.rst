Update Plugin
===================

The update plugin is used to manage the current pychron version. It uses Git as a backend for
version control and distribution.

pychron stores its source code in a git repository located at [pychron_root]/.hidden/pychron

if the repo doesn't exist it is cloned. The source code repository name and default branch are stored in preferences.
Default values of ``NMGRL/pychron`` and ``master`` are provided.

Update Process
----------------
- check for updates

  - compare the local commit to the remote commit

- if updates available

  - pull updates
  - build egg and resources
  - move egg and resources into the application bundle.