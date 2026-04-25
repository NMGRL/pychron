from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

from git import NoSuchPathError

from pychron.core.progress import progress_iterator
from pychron.dvc import repository_path
from pychron.dvc.meta_repo import get_frozen_flux, get_frozen_productions
from pychron.git_archive.repo_manager import get_repository_branch
from pychron.pychron_constants import DATE_FORMAT


@dataclass
class AnalysisLoadContext:
    branches: dict[str, str] = field(default_factory=dict)
    flux_histories: dict[str, Optional[str]] = field(default_factory=dict)
    fluxes: dict[str, dict[str, Any]] = field(default_factory=dict)
    productions: dict[str, dict[str, Any]] = field(default_factory=dict)
    chronos: dict[str, Any] = field(default_factory=dict)
    sensitivities: dict[str, Any] = field(default_factory=dict)
    frozen_fluxes: dict[str, Any] = field(default_factory=dict)
    frozen_productions: dict[str, Any] = field(default_factory=dict)
    sample_prep: dict[str, Any] = field(default_factory=dict)


def partition_cached_records(
    dvc: Any, records: Iterable[Any], use_cached: bool
) -> tuple[list[Any], list[Any]]:
    cached_records: list[Any] = []
    if not (dvc.use_cache and use_cached):
        return list(records), cached_records

    pending: list[Any] = []
    cache = dvc._cache
    for record in records:
        cached = cache.get(record.uuid)
        if cached is not None:
            cached_records.append(cached)
        else:
            pending.append(record)

    return pending, cached_records


def filter_records_with_repository(
    dvc: Any, records: list[Any], warn: bool = True
) -> list[Any]:
    bad_records = [r for r in records if r.repository_identifier is None]
    if bad_records and warn:
        dvc.warning_dialog(
            "Missing Repository Associations. Contact an expert!"
            'Cannot load analyses "{}"'.format(
                ",".join([r.record_id for r in bad_records])
            )
        )

    return [r for r in records if r.repository_identifier is not None]


def sync_analysis_repositories(
    dvc: Any,
    exps: Iterable[str],
    use_progress: bool = True,
    pull_frequency: Optional[int] = None,
) -> None:
    def func(name: str, prog: Any, i: int, n: int) -> None:
        if prog:
            prog.change_message("Syncing repository= {}".format(name))
        try:
            dvc.sync_repo(name, use_progress=False, pull_frequency=pull_frequency)
        except BaseException as e:
            dvc.debug("sync repo failed for %s: %s", name, e)

    if use_progress:
        progress_iterator(exps, func, threshold=1)
    else:
        for exp in exps:
            func(exp, None, 0, 0)


def prepare_repository_branches(
    dvc: Any,
    exps: Iterable[str],
    sync_repo: bool = True,
    use_progress: bool = True,
    pull_frequency: Optional[int] = None,
) -> Optional[dict[str, str]]:
    if sync_repo:
        sync_analysis_repositories(
            dvc, exps, use_progress=use_progress, pull_frequency=pull_frequency
        )

    try:
        return {exp: get_repository_branch(repository_path(exp)) for exp in exps}
    except NoSuchPathError as e:
        dvc.warning("Repository path missing while loading analyses: %s", e)
        return None


def build_analysis_load_context(
    dvc: Any,
    records: list[Any],
    exps: Iterable[str],
    branches: dict[str, str],
    quick: bool = False,
    use_flux_histories: bool = True,
) -> AnalysisLoadContext:
    context = AnalysisLoadContext(branches=branches)
    if quick:
        return context

    meta_repo = dvc.meta_repo
    use_cocktail_irradiation = dvc.use_cocktail_irradiation
    irrad_levels = {
        (record.repository_identifier, record.irradiation, record.irradiation_level)
        for record in records
        if record.irradiation != "NoIrradiation"
    }

    for exp in exps:
        context.frozen_productions.update(get_frozen_productions(exp))

    for repository_identifier, irrad, level in irrad_levels:
        if irrad not in context.frozen_fluxes:
            context.frozen_fluxes[irrad] = get_frozen_flux(
                repository_identifier, irrad
            )

        flux_levels = context.fluxes.setdefault(irrad, {})
        prod_levels = context.productions.setdefault(irrad, {})
        flux_levels[level] = meta_repo.get_flux_positions(irrad, level)
        prod_levels[level] = meta_repo.get_production(irrad, level)

        if irrad not in context.chronos:
            context.chronos[irrad] = meta_repo.get_chronology(irrad)

        if use_flux_histories:
            key = "{}{}".format(irrad, level)
            history = meta_repo.get_flux_history(irrad, level, max_count=1)
            value = None
            if history:
                history = history[0]
                value = "{} ({})".format(
                    history.date.strftime(DATE_FORMAT), history.author
                )
            context.flux_histories[key] = value

    has_cocktail = any(record.analysis_type == "cocktail" for record in records)
    if has_cocktail and use_cocktail_irradiation:
        cirr = meta_repo.get_cocktail_irradiation()
        context.chronos["cocktail"] = cirr.get("chronology")
        context.fluxes["cocktail"] = cirr.get("flux")

    context.sensitivities = meta_repo.get_sensitivities()
    return context


def finalize_loaded_analyses(
    dvc: Any, analyses: list[Any], cached_records: list[Any]
) -> list[Any]:
    if dvc.use_cache:
        dvc._cache.clean()
        analyses = cached_records + analyses
    return analyses
