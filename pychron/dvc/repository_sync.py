from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from pychron.dvc import DATA_COLLECTION_BRANCH, repository_path
from pychron.dvc.func import push_repositories as push_repository_changes
from pychron.git.hosts import IGitHost
from pychron.git.hosts.local import LocalGitHostService


def clear_pull_cache(dvc: Any) -> None:
    dvc._pull_cache = {}


def is_clean(dvc: Any, name: str) -> bool:
    try:
        repo = dvc._get_repository(name)
        ahead, behind = repo.ahead_behind()
        return ahead == 0 and behind == 0
    except BaseException as e:
        dvc.debug("is clean exception {}".format(e))
        return False


def _recover_clean_state(dvc: Any, name: str) -> bool:
    """
    Try to recover a clean repository state by resetting to match the remote.
    This is needed when a repo has diverged (commits ahead or behind).
    
    Returns True if successfully cleaned, False otherwise.
    """
    try:
        repo = dvc._get_repository(name)
        ahead, behind = repo.ahead_behind()
        dvc.debug(f"Attempting to clean repository '{name}': ahead={ahead}, behind={behind}")
        
        if ahead == 0 and behind == 0:
            return True
        
        # Try to fetch fresh data from remote
        try:
            repo._repo.remotes.origin.fetch()
            dvc.debug(f"Fetched from remote for '{name}'")
        except Exception as e:
            dvc.debug(f"Fetch failed for '{name}': {e}")
        
        # Check status again
        ahead, behind = repo.ahead_behind()
        if ahead == 0 and behind == 0:
            return True
        
        # If still behind, try another pull
        if behind > 0:
            try:
                repo.pull(use_progress=False)
                ahead, behind = repo.ahead_behind()
                if ahead == 0 and behind == 0:
                    dvc.debug(f"Repository '{name}' cleaned via additional pull")
                    return True
            except Exception as e:
                dvc.debug(f"Additional pull failed for '{name}': {e}")
        
        # If still ahead (unpushed commits), reset to remote
        if ahead > 0:
            try:
                current_branch = repo._repo.active_branch
                remote_ref = repo._repo.remotes.origin.refs[current_branch.name]
                repo._repo.head.reset(index=True, working_tree=True)
                repo._repo.remotes.origin.pull()
                dvc.debug(f"Repository '{name}' reset to match remote (discarded {ahead} local commits)")
                return True
            except Exception as e:
                dvc.debug(f"Reset to remote failed for '{name}': {e}")
        
        return False
    except Exception as e:
        dvc.debug(f"Failed to recover clean state for '{name}': {e}")
        return False


def sync_repo(
    dvc: Any, name: str, use_progress: bool = True, pull_frequency: int | None = None
) -> bool | None:
    """
    Pull or clone a repository and then sync reduction branches from data collection.
    """
    root = repository_path(name)
    exists = os.path.isdir(os.path.join(root, ".git"))
    dvc.debug(
        "sync repository {}. exists={} pull_frequency={}".format(
            name, exists, pull_frequency
        )
    )

    if exists:
        if pull_frequency:
            now = datetime.now()
            last_pull = dvc._pull_cache.get(name)
            dvc._pull_cache[name] = now

            elapsed = None if last_pull is None else (now - last_pull).seconds
            dvc.debug("last_pull={} elapsed={} skip={}".format(last_pull, elapsed, bool(elapsed and elapsed < pull_frequency)))
            if elapsed is not None and elapsed < pull_frequency:
                return True

        try:
            repo = dvc._get_repository(name)
            repo.pull(use_progress=use_progress, use_auto_pull=dvc.use_auto_pull)
            sync_repo_from_data_collection(dvc, repo)
            return True
        except Exception as e:
            dvc.warning(f"Failed to pull/sync repository '{name}': {e}")
            dvc.debug(f"Pull error details for '{name}'", exc_info=True)
            return False

    dvc.debug("getting repository from remote")

    service = dvc.git_service or dvc.application.get_service(IGitHost)
    if not service:
        return True

    if isinstance(service, LocalGitHostService):
        service.create_empty_repo(name)
        return True

    try:
        if service.clone_from(name, root, dvc.organization):
            repo = dvc._get_repository(name)
            sync_repo_from_data_collection(dvc, repo)
            return True
    except Exception as e:
        dvc.warning(f"Failed to clone repository '{name}': {e}")
        dvc.debug(f"Clone error details for '{name}'", exc_info=True)

    dvc.warning_dialog(
        "name={} not in available repos "
        "from service={}, organization={}".format(
            name, service.remote_url, dvc.organization
        )
    )
    names = dvc.remote_repository_names()
    for ni in names:
        dvc.debug("available repo== {}".format(ni))

    return None


def sync_repo_from_data_collection(
    dvc: Any, repo_or_name: Any, remote: str = "origin", inform: bool = False
) -> bool:
    if isinstance(repo_or_name, str):
        repo = dvc._get_repository(repo_or_name)
    else:
        repo = repo_or_name

    return sync_reduction_repo_from_data_collection(
        dvc, repo, remote=remote, inform=inform
    )


def sync_reduction_repo_from_data_collection(
    dvc: Any, repo: Any, remote: str = "origin", inform: bool = False
) -> bool:
    branch = repo.get_current_branch()
    if branch == DATA_COLLECTION_BRANCH:
        dvc.debug(
            "skip data_collection sync for %s. current branch is append-only %s",
            repo.name,
            DATA_COLLECTION_BRANCH,
        )
        return False

    if not repo.has_remote(remote):
        dvc.debug(
            "skip data_collection sync for %s. missing remote %s", repo.name, remote
        )
        return False

    if not has_remote_data_collection_branch(dvc, repo, remote):
        dvc.debug(
            "skip data_collection sync for %s. no %s/%s branch",
            repo.name,
            remote,
            DATA_COLLECTION_BRANCH,
        )
        return False

    target = "{}/{}".format(remote, DATA_COLLECTION_BRANCH)
    dvc.debug(
        'sync reduction branch "%s" from "%s" for repository %s',
        branch,
        target,
        repo.name,
    )
    try:
        repo.fetch(remote)
        repo.merge(target, inform=inform)
        return True
    except BaseException:
        dvc.debug_exception()
        dvc.debug(
            "sync from %s failed for %s. This can be expected for local-only repos.",
            target,
            repo.name,
        )
        return False


def has_remote_data_collection_branch(
    dvc: Any, repo: Any, remote: str = "origin"
) -> bool:
    try:
        branches = repo.cmd("branch", "-r") or ""
    except BaseException:
        dvc.debug_exception()
        return False

    target = "{}/{}".format(remote, DATA_COLLECTION_BRANCH)
    for line in branches.splitlines():
        line = line.strip()
        if line == target or line.endswith(" -> {}".format(target)):
            return True

    return False


def pull_repository(dvc: Any, repo: Any) -> None:
    repository = dvc._get_repository(repo)
    dvc.debug("pull repository {}".format(repository))
    for gi in dvc.application.get_services(IGitHost):
        dvc.debug("pull to remote={}, url={}".format(gi.default_remote_name, gi.remote_url))
        repository.smart_pull(remote=gi.default_remote_name)


def push_repository(dvc: Any, repo: Any, **kw: Any) -> None:
    repository = dvc._get_repository(repo)
    dvc.debug("push repository {}".format(repository))
    for gi in dvc.application.get_services(IGitHost):
        dvc.debug(
            "pushing to remote={}, url={}".format(
                gi.default_remote_name, gi.remote_url
            )
        )
        repository.push(remote=gi.default_remote_name, **kw)


def push_repositories(dvc: Any, changes: list[Any]) -> None:
    if dvc.use_auto_push or dvc.confirmation_dialog(
        "Would you like to push (share) your changes?"
    ):
        for gi in dvc.application.get_services(IGitHost):
            push_repository_changes(changes, gi, quiet=False)


def delete_local_commits(dvc: Any, repo: Any, **kw: Any) -> None:
    repository = dvc._get_repository(repo)
    repository.delete_local_commits(**kw)
