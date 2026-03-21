from dataclasses import dataclass


@dataclass(frozen=True)
class StarterBundle:
    name: str
    version: str
    description: str
    profiles: tuple[str, ...]
    notes: tuple[str, ...] = ()


BUNDLES = {
    "data-reduction": StarterBundle(
        name="data-reduction",
        version="2026.1",
        description="Reduction workstation with plotting and pipeline defaults.",
        profiles=("data-reduction",),
        notes=(
            "Best for analysis/review machines that do not control hardware.",
        ),
    ),
    "experiment-control": StarterBundle(
        name="experiment-control",
        version="2026.1",
        description="Automated experiment execution with queue and script support.",
        profiles=("experiment",),
    ),
    "extraction-line": StarterBundle(
        name="extraction-line",
        version="2026.1",
        description="Extraction-line control and monitoring workstation.",
        profiles=("extraction-line",),
    ),
    "ngx-collection": StarterBundle(
        name="ngx-collection",
        version="2026.1",
        description="NGX collection workstation with spectrometer defaults.",
        profiles=("experiment", "ngx"),
        notes=(
            "Use on acquisition machines that need NGX-specific config stubs.",
        ),
    ),
    "chromiumco2-lab": StarterBundle(
        name="chromiumco2-lab",
        version="2026.1",
        description="Chromium CO2 laser workstation derived from common consulting layouts.",
        profiles=("chromiumco2",),
    ),
    "chromiumdiode-lab": StarterBundle(
        name="chromiumdiode-lab",
        version="2026.1",
        description="Chromium diode laser workstation derived from common consulting layouts.",
        profiles=("chromiumdiode",),
    ),
}


ALIASES = {
    "reduction": "data-reduction",
    "experiment": "experiment-control",
    "ngx": "ngx-collection",
    "chromiumco2": "chromiumco2-lab",
    "chromiumdiode": "chromiumdiode-lab",
}


def available_bundle_names():
    return tuple(sorted(BUNDLES))


def normalize_bundle_name(name):
    return name.strip().lower()


def resolve_bundle_name(name):
    normalized = normalize_bundle_name(name)
    return ALIASES.get(normalized, normalized)


def resolve_bundles(names):
    bundles = []
    seen = set()
    for name in names or ():
        resolved = resolve_bundle_name(name)
        if resolved in seen:
            continue

        try:
            bundle = BUNDLES[resolved]
        except KeyError as exc:
            raise KeyError('Unknown bundle "{}"'.format(name)) from exc

        seen.add(resolved)
        bundles.append(bundle)

    return bundles


def bundle_profiles(names):
    profiles = []
    seen = set()
    for bundle in resolve_bundles(names):
        for profile in bundle.profiles:
            if profile not in seen:
                seen.add(profile)
                profiles.append(profile)
    return tuple(profiles)
