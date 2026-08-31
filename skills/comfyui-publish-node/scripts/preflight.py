#!/usr/bin/env python3
"""Read-only preflight for `comfy node publish`.

Run from the node pack root (the directory holding pyproject.toml):

    uv run --no-project --python 3.11 scripts/preflight.py
    python3 scripts/preflight.py          # needs Python >= 3.11 for tomllib

Checks pyproject metadata, registry version collision, git packaging state, and
whether a secret file would be swept into the uploaded archive. Never reads,
prints, or touches the registry token. Exits 1 if any hard check fails.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:
        sys.exit(
            "Need Python >= 3.11 (for tomllib) or `pip install tomli`.\n"
            "Try: uv run --no-project --python 3.11 scripts/preflight.py"
        )

REGISTRY_API = "https://api.comfy.org/nodes/{name}"

# Registry rules: <100 chars, alphanumeric/-/_/., no leading digit or special
# char, no consecutive special characters.
NAME_RE = re.compile(r"^[A-Za-z](?:[A-Za-z0-9]|[-_.](?![-_.]))*$")
SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")

SECRET_GLOBS = (".env", ".env.*", "*.pem", "*.key", "credentials.json", "*.credentials")

errors: list[str] = []
warnings: list[str] = []
notes: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def note(msg: str) -> None:
    notes.append(msg)


def git(*args: str) -> str | None:
    """Run a git command, or return None when git can't answer."""
    try:
        out = subprocess.run(
            ["git", *args], capture_output=True, text=True, check=False
        )
    except (FileNotFoundError, OSError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout


def load_pyproject() -> dict:
    path = Path("pyproject.toml")
    if not path.is_file():
        sys.exit(
            "No pyproject.toml in this directory. Run from the node pack root, or `comfy node init`."
        )
    try:
        with path.open("rb") as fh:
            return tomllib.load(fh)
    except Exception as exc:  # noqa: BLE001 - surface the parse error verbatim
        sys.exit(f"pyproject.toml does not parse: {exc}")


def check_metadata(cfg: dict) -> tuple[str | None, str | None]:
    project = cfg.get("project") or {}
    comfy = (cfg.get("tool") or {}).get("comfy") or {}

    name = project.get("name")
    version = project.get("version")
    repository = (project.get("urls") or {}).get("Repository")
    publisher = comfy.get("PublisherId")

    if not name:
        fail(
            "`project.name` is missing. It is the permanent registry id and cannot be changed later."
        )
    elif len(name) >= 100:
        fail(f"`project.name` is {len(name)} chars; the registry limit is under 100.")
    elif not NAME_RE.match(name):
        fail(
            f"`project.name` = {name!r} breaks registry naming rules: letters, digits, "
            "'-', '_', '.' only; must start with a letter; no consecutive special characters."
        )

    if not version:
        fail(
            "`project.version` is empty. Set it, or configure `[tool.comfy.version].path` "
            'if using dynamic = ["version"].'
        )
    elif not SEMVER_RE.match(version):
        fail(f"`project.version` = {version!r} is not semver X.Y.Z.")

    if not repository:
        fail("`[project.urls] Repository` is required.")
    if not publisher:
        fail(
            "`[tool.comfy] PublisherId` is required. Find it on your registry.comfy.org publisher page."
        )

    for optional, label in (("DisplayName", "DisplayName"), ("Icon", "Icon")):
        if not comfy.get(optional):
            note(
                f"[tool.comfy] {label} not set (optional, but it is what users see in the manager)."
            )

    license_field = project.get("license")
    if license_field is None:
        note("`project.license` not set; comfy-cli warns about this at publish time.")
    elif not (
        isinstance(license_field, dict)
        and ("file" in license_field or "text" in license_field)
    ):
        warn(
            '`project.license` must be { file = "LICENSE" } or { text = "MIT License" }; '
            "comfy-cli warns on any other form."
        )

    if name and version:
        print(f"  package : {name} {version}")
    if publisher:
        print(f"  publisher: {publisher}")

    return name, version


def check_registry_version(name: str | None, version: str | None) -> None:
    if not name or not version or not SEMVER_RE.match(version):
        return
    url = REGISTRY_API.format(name=name.lower())
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            note(
                f"'{name}' is not on the registry yet - this would be the first publish."
            )
        else:
            warn(
                f"Could not reach the registry ({exc.code}); version collision not verified."
            )
        return
    except Exception as exc:  # noqa: BLE001 - network shape varies
        warn(f"Could not reach the registry ({exc}); version collision not verified.")
        return

    published = ((data.get("latest_version") or {}).get("version")) or ""
    if not published:
        note(f"'{name}' exists on the registry but reports no published version.")
        return

    print(f"  registry : latest published is {published}")
    local_match = SEMVER_RE.match(version)
    remote_match = SEMVER_RE.match(published)
    if not local_match or not remote_match:
        return
    local = tuple(int(p) for p in local_match.groups())
    remote = tuple(int(p) for p in remote_match.groups())

    if local == remote:
        fail(
            f"Version {version} is already published. A version can never be republished - bump it."
        )
    elif local < remote:
        fail(
            f"Local version {version} is behind the published {published}. Bump past it."
        )


def check_git_and_secrets() -> None:
    tracked = git("ls-files")
    in_repo = tracked is not None

    secrets = sorted(
        {
            str(p)
            for pattern in SECRET_GLOBS
            for p in Path().glob(pattern)
            if p.is_file()
        }
    )

    if not in_repo:
        fail(
            "Not a git repository (or git is unavailable). comfy-cli then zips EVERY file in "
            "this directory and uploads it to the public registry."
        )
        if secrets:
            fail(
                "Secret-looking files present that would be uploaded: "
                + ", ".join(secrets)
                + ". Fix git, or move these out of the directory, before publishing."
            )
        return

    files = [line for line in tracked.splitlines() if line.strip()]
    print(f"  archive  : {len(files)} git-tracked files")

    for secret in secrets:
        if secret in files:
            fail(
                f"{secret} is git-tracked and WOULD be uploaded to the public registry. Untrack it."
            )
        elif secret == ".env":
            ignored = subprocess.run(
                ["git", "check-ignore", "-q", ".env"], capture_output=True, check=False
            )
            if ignored.returncode != 0:
                warn(".env exists and is not gitignored. Add it to .gitignore.")

    untracked = git("ls-files", "--others", "--exclude-standard") or ""
    untracked_files = [line for line in untracked.splitlines() if line.strip()]
    if untracked_files:
        shown = ", ".join(untracked_files[:10])
        more = (
            f" (+{len(untracked_files) - 10} more)" if len(untracked_files) > 10 else ""
        )
        warn(
            f"{len(untracked_files)} untracked file(s) will be EXCLUDED from the archive: "
            f"{shown}{more}. `git add` anything the release needs."
        )

    modified = git("diff", "--name-only") or ""
    modified_files = [line for line in modified.splitlines() if line.strip()]
    if modified_files:
        note(
            f"{len(modified_files)} tracked file(s) have uncommitted changes; the working-tree "
            "version is what gets packaged."
        )


def main() -> int:
    print("Preflight for comfy node publish")
    cfg = load_pyproject()
    name, version = check_metadata(cfg)
    check_registry_version(name, version)
    check_git_and_secrets()

    print()
    for msg in notes:
        print(f"note  : {msg}")
    for msg in warnings:
        print(f"WARN  : {msg}")
    for msg in errors:
        print(f"ERROR : {msg}")

    print()
    if errors:
        print(f"FAILED - {len(errors)} blocking issue(s). Do not publish.")
        return 1
    if warnings:
        print(f"PASSED with {len(warnings)} warning(s). Review before publishing.")
        return 0
    print("PASSED - ready to publish.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
