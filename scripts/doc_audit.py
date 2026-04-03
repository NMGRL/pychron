#!/usr/bin/env python3
"""
doc_audit.py — Documentation maintenance audit script.

For each code change that touches a mapped module, calls the Claude API to
identify what needs updating in the corresponding documentation guide.

Usage:
    python scripts/doc_audit.py \
        --changed-files-file /tmp/changed_files.txt \
        --sha abc1234 \
        --output docs/auto-update-summary.md \
        [--repo-root .] \
        [--doc-map docs/doc-map.json] \
        [--max-diff-lines 400] \
        [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import textwrap
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class DocMapping:
    id: str
    document: str
    doc_file: str
    description: str
    path_prefixes: list[str]


@dataclass
class AffectedDoc:
    mapping: DocMapping
    changed_files: list[str] = field(default_factory=list)
    diffs: dict[str, str] = field(default_factory=dict)
    suggestion: Optional[str] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Doc-map loading
# ---------------------------------------------------------------------------


def load_doc_map(path: Path) -> list[DocMapping]:
    try:
        with open(path) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: doc-map not found at {path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON in doc-map: {e}", file=sys.stderr)
        sys.exit(1)

    mappings = []
    for entry in data.get("mappings", []):
        mappings.append(
            DocMapping(
                id=entry["id"],
                document=entry["document"],
                doc_file=entry["doc_file"],
                description=entry["description"],
                path_prefixes=entry["path_prefixes"],
            )
        )
    return mappings


# ---------------------------------------------------------------------------
# File → doc mapping
# ---------------------------------------------------------------------------


def map_files_to_docs(
    changed_files: list[str], mappings: list[DocMapping]
) -> list[AffectedDoc]:
    """Return one AffectedDoc per mapping that has at least one matching file."""
    affected: dict[str, AffectedDoc] = {}

    for filepath in changed_files:
        for mapping in mappings:
            if any(filepath.startswith(prefix) for prefix in mapping.path_prefixes):
                if mapping.id not in affected:
                    affected[mapping.id] = AffectedDoc(mapping=mapping)
                affected[mapping.id].changed_files.append(filepath)

    return list(affected.values())


# ---------------------------------------------------------------------------
# Git diff helpers
# ---------------------------------------------------------------------------


def get_file_diff(
    filepath: str,
    before_sha: Optional[str],
    repo_root: Path,
    max_lines: int,
) -> str:
    """
    Return the unified diff for a single file.

    Falls back gracefully: if before_sha is unavailable (first commit),
    shows the full file content instead.
    """
    try:
        if before_sha:
            result = subprocess.run(
                ["git", "diff", before_sha, "HEAD", "--", filepath],
                capture_output=True,
                text=True,
                cwd=repo_root,
                timeout=30,
            )
        else:
            # First commit — show full file
            result = subprocess.run(
                ["git", "show", f"HEAD:{filepath}"],
                capture_output=True,
                text=True,
                cwd=repo_root,
                timeout=30,
            )
    except subprocess.TimeoutExpired:
        return f"[diff timed out for {filepath}]"
    except Exception as e:
        return f"[error getting diff for {filepath}: {e}]"

    if result.returncode != 0:
        stderr = result.stderr.strip()
        # File may have been deleted; that's fine — return a note.
        if "does not exist" in stderr or result.stdout == "":
            return f"[file deleted or not found: {filepath}]"
        return f"[git diff error for {filepath}: {stderr}]"

    diff_text = result.stdout
    if not diff_text.strip():
        return f"[no textual diff for {filepath} — possible binary or rename]"

    lines = diff_text.splitlines()
    if len(lines) > max_lines:
        truncated = lines[:max_lines]
        truncated.append(
            f"\n... [truncated: {len(lines) - max_lines} additional lines not shown] ..."
        )
        return "\n".join(truncated)

    return diff_text


def collect_diffs(
    affected_doc: AffectedDoc,
    before_sha: Optional[str],
    repo_root: Path,
    max_diff_lines: int,
) -> None:
    """Populate affected_doc.diffs in place."""
    for filepath in affected_doc.changed_files:
        diff = get_file_diff(filepath, before_sha, repo_root, max_diff_lines)
        affected_doc.diffs[filepath] = diff


# ---------------------------------------------------------------------------
# Claude API call
# ---------------------------------------------------------------------------

# Maximum characters of combined diff to send in a single API call.
# ~200k chars ≈ ~50k tokens, well within claude-sonnet-4 context.
MAX_DIFF_CHARS = 180_000


def build_prompt(affected_doc: AffectedDoc) -> str:
    mapping = affected_doc.mapping

    diff_sections = []
    total_chars = 0
    for filepath, diff in affected_doc.diffs.items():
        section = f"### `{filepath}`\n\n```diff\n{diff}\n```\n"
        total_chars += len(section)
        if total_chars > MAX_DIFF_CHARS:
            diff_sections.append(
                f"### `{filepath}`\n\n[omitted — combined diff exceeded size limit]\n"
            )
        else:
            diff_sections.append(section)

    diffs_text = "\n".join(diff_sections)

    return textwrap.dedent(f"""
        You are a technical documentation reviewer for Pychron, an open-source noble gas
        mass spectrometry platform used in geochronology labs.

        The following source files were changed in a recent commit to the `main` branch.
        These files fall under the scope of the **{mapping.document}**.

        **Document description:**
        {mapping.description}

        **Document file:** `{mapping.doc_file}`

        ---

        **Changed files and their diffs:**

        {diffs_text}

        ---

        **Your task:**

        Review these code changes and identify *specifically* what needs to be updated in the
        **{mapping.document}**. Do not suggest general improvements — only flag things that
        are now incorrect, incomplete, or missing because of these specific changes.

        Respond in this exact format:

        ## Code Change Summary
        (2–4 sentences describing what changed in the code and why it matters for documentation)

        ## Documentation Updates Required

        For each update needed, use this structure:
        - **Section/Topic:** [which section or topic in the doc needs updating]
          **Issue:** [what is now wrong or missing]
          **Suggested update:** [what the correct information should say, as specifically as possible]

        If no documentation updates are needed for these changes, respond with:
        ## No Updates Required
        (brief explanation of why these changes don't affect the documentation)
    """).strip()


def call_claude(affected_doc: AffectedDoc, api_key: str, model: str) -> None:
    """Call the Claude API and store the suggestion on affected_doc in place."""
    try:
        import anthropic
    except ImportError:
        affected_doc.error = (
            "anthropic package not installed. Run: pip install anthropic"
        )
        return

    client = anthropic.Anthropic(api_key=api_key)
    prompt = build_prompt(affected_doc)

    try:
        message = client.messages.create(
            model=model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        affected_doc.suggestion = message.content[0].text
    except anthropic.AuthenticationError:
        affected_doc.error = "Claude API authentication failed — check ANTHROPIC_API_KEY secret."
    except anthropic.RateLimitError:
        affected_doc.error = "Claude API rate limit exceeded. Re-run the workflow or increase retry delay."
    except anthropic.APIStatusError as e:
        affected_doc.error = f"Claude API error (HTTP {e.status_code}): {e.message}"
    except Exception as e:
        affected_doc.error = f"Unexpected error calling Claude API: {e}"


# ---------------------------------------------------------------------------
# Markdown report generation
# ---------------------------------------------------------------------------


def render_markdown(
    affected_docs: list[AffectedDoc],
    sha: str,
    all_changed_files: list[str],
    before_sha: Optional[str],
) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    compare_url_fragment = (
        f"compare/{before_sha}...{sha}" if before_sha else f"commit/{sha}"
    )

    lines: list[str] = []

    lines.append("# Documentation Update Review")
    lines.append("")
    lines.append(
        f"**Triggered by commit:** `{sha}`  "
    )
    lines.append(f"**Generated:** {now}  ")
    lines.append(
        f"**Compare:** [`{before_sha or 'initial'}...{sha}`]"
        f"(../../{compare_url_fragment})"
    )
    lines.append("")

    # Quick-reference table
    lines.append("## Affected Documents")
    lines.append("")
    lines.append("| Document | Files Changed | Status |")
    lines.append("|---|---|---|")
    for ad in affected_docs:
        status = "⚠️ API error" if ad.error else "✅ Reviewed"
        file_count = len(ad.changed_files)
        lines.append(
            f"| [{ad.mapping.document}](#{ad.mapping.id}) "
            f"| {file_count} file{'s' if file_count != 1 else ''} "
            f"| {status} |"
        )
    lines.append("")

    # All changed files (for context)
    lines.append("## All Changed Files in This Commit")
    lines.append("")
    lines.append("<details>")
    lines.append("<summary>Click to expand</summary>")
    lines.append("")
    lines.append("```")
    for f in sorted(all_changed_files):
        lines.append(f)
    lines.append("```")
    lines.append("")
    lines.append("</details>")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Per-document sections
    for ad in affected_docs:
        m = ad.mapping
        lines.append(f"## {m.document} {{#{m.id}}}")
        lines.append("")
        lines.append(f"**Doc file:** `{m.doc_file}`  ")
        lines.append(f"**Matched prefixes:** {', '.join(f'`{p}`' for p in m.path_prefixes)}")
        lines.append("")

        lines.append("### Changed Files")
        lines.append("")
        for filepath in ad.changed_files:
            lines.append(f"- `{filepath}`")
        lines.append("")

        if ad.error:
            lines.append("### ⚠️ Review Error")
            lines.append("")
            lines.append(f"> {ad.error}")
            lines.append("")
            lines.append(
                "_Manual review required. Inspect the changed files above against "
                f"the [{m.document}]({m.doc_file})._"
            )
        elif ad.suggestion:
            lines.append("### AI Review")
            lines.append("")
            lines.append(ad.suggestion)
        else:
            lines.append("### Review")
            lines.append("")
            lines.append("_No suggestion generated._")

        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append(
        "_This file was auto-generated by `scripts/doc_audit.py`. "
        "A human must review and apply any changes to the documentation._"
    )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit documentation impact of code changes using Claude."
    )
    parser.add_argument(
        "--changed-files-file",
        required=True,
        help="Path to a newline-delimited text file listing changed file paths.",
    )
    parser.add_argument(
        "--sha",
        required=True,
        help="Short SHA of the current HEAD commit (used for branch naming and output).",
    )
    parser.add_argument(
        "--before-sha",
        default=None,
        help="SHA of the previous commit. Used for git diff. Omit for initial commit.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path where the markdown summary file will be written.",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Root of the git repository (default: current directory).",
    )
    parser.add_argument(
        "--doc-map",
        default="docs/doc-map.json",
        help="Path to the doc-map.json file (default: docs/doc-map.json).",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-20250514",
        help="Anthropic model ID to use (default: claude-sonnet-4-20250514).",
    )
    parser.add_argument(
        "--max-diff-lines",
        type=int,
        default=400,
        help="Maximum lines of diff to include per file before truncating (default: 400).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build prompts and report structure but skip the Claude API calls.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    repo_root = Path(args.repo_root).resolve()
    doc_map_path = repo_root / args.doc_map
    output_path = Path(args.output)

    # --- Read changed files ---
    changed_files_path = Path(args.changed_files_file)
    if not changed_files_path.exists():
        print(f"ERROR: changed-files-file not found: {changed_files_path}", file=sys.stderr)
        return 1

    changed_files = [
        line.strip()
        for line in changed_files_path.read_text().splitlines()
        if line.strip()
    ]

    if not changed_files:
        print("No changed files found. Nothing to audit.")
        return 0

    print(f"Changed files ({len(changed_files)}):")
    for f in changed_files:
        print(f"  {f}")

    # --- Load doc map ---
    mappings = load_doc_map(doc_map_path)
    print(f"\nLoaded {len(mappings)} doc mappings from {doc_map_path}")

    # --- Map files to docs ---
    affected_docs = map_files_to_docs(changed_files, mappings)

    if not affected_docs:
        print("\nNo changed files match any documented module. No PR needed.")
        return 0

    print(f"\nAffected documents ({len(affected_docs)}):")
    for ad in affected_docs:
        print(f"  {ad.mapping.document} ({len(ad.changed_files)} files)")

    # --- Collect diffs ---
    print("\nCollecting diffs...")
    for ad in affected_docs:
        collect_diffs(ad, args.before_sha, repo_root, args.max_diff_lines)

    # --- Call Claude ---
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key and not args.dry_run:
        print(
            "ERROR: ANTHROPIC_API_KEY environment variable not set.",
            file=sys.stderr,
        )
        return 1

    for ad in affected_docs:
        if args.dry_run:
            print(f"\n[dry-run] Skipping Claude call for: {ad.mapping.document}")
            ad.suggestion = "_Dry run — Claude API call skipped._"
        else:
            print(f"\nCalling Claude for: {ad.mapping.document} ...")
            call_claude(ad, api_key, args.model)
            if ad.error:
                print(f"  WARNING: {ad.error}")
            else:
                print(f"  Done.")

    # --- Write output ---
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report = render_markdown(affected_docs, args.sha, changed_files, args.before_sha)
    output_path.write_text(report)
    print(f"\nReport written to: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
