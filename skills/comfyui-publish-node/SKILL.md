---
name: comfyui-publish-node
description: >
  Publish a ComfyUI custom node pack to the Comfy Registry (registry.comfy.org) with
  `uvx comfy-cli node publish`, resolving the Personal Access Token from the environment
  or a local `.env` and refusing to publish when no token is configured. Use this skill
  whenever the user wants to publish, release, or ship a ComfyUI custom node or node pack,
  bump a node version and push it to the registry, set up the publish GitHub Action, or
  debug a failed publish. Also trigger on "comfy node publish", "comfy-cli publish",
  "publish to Comfy Registry", "REGISTRY_ACCESS_TOKEN", "PublisherId", "registry.comfy.org",
  "publish my custom node", or "release my ComfyUI node".
---

# Publishing ComfyUI Custom Nodes to the Comfy Registry

Publishing is **irreversible and public**. A version number, once accepted, can never be
re-published or overwritten — a mistake is fixable only by shipping a new version. The
uploaded archive is downloadable by anyone. Treat everything below as preflight for a
one-way action.

---

## Token rules — read before anything else

The Personal Access Token is a credential that publishes under the user's publisher
identity. These rules are absolute.

1. **Never ask the user to paste the token into the chat.** If it is not already in the
   environment or `.env`, stop and tell them how to set it (Step 1). Do not offer to
   receive it in a message.
2. **Never type the token value into a command.** Always pass it by shell variable
   expansion — `--token "$TOKEN"` — so the command text echoed into the transcript, logs,
   and shell history holds the variable name, not the secret.
3. **Never print, echo, `cat`, or log the token**, not even a prefix or the first few
   characters. To confirm it exists, report its length or the word `set` — nothing derived
   from its content.
4. **Never write the token to a file**, never put it in `pyproject.toml`, a workflow file,
   a commit, or a comment.
5. **Never fall back to the interactive prompt.** Without `--token`, `comfy node publish`
   prompts for the API key on stdin; in a non-interactive tool call that hangs or fails.
   Always pass `--token`.
6. **If no token is configured, reject the publish.** Do not guess, do not go hunting the
   filesystem for credentials, do not prompt. Stop at Step 1.

---

## Step 1 — Resolve the token (environment first, then `.env`, else reject)

Accepted variable names, in priority order:

| Name | Notes |
|---|---|
| `REGISTRY_ACCESS_TOKEN` | Primary — the name the official GitHub Action uses |
| `COMFY_REGISTRY_TOKEN` | Alias |
| `COMFY_API_KEY` | Alias |

Resolution order is **process environment → `.env` in the node pack root → reject**. Do
not read `.env` files outside the node pack directory, and do not read shell profiles.

Check availability without revealing anything:

```bash
for v in REGISTRY_ACCESS_TOKEN COMFY_REGISTRY_TOKEN COMFY_API_KEY; do
  eval "val=\${$v:-}"
  if [ -n "$val" ]; then echo "env $v: set (${#val} chars)"; else echo "env $v: unset"; fi
done
if [ -f .env ]; then
  echo ".env: present, $(grep -acE '^[[:space:]]*(REGISTRY_ACCESS_TOKEN|COMFY_REGISTRY_TOKEN|COMFY_API_KEY)=' .env) matching entries"
else
  echo ".env: not present"
fi
```

### If nothing is set — stop here

Do not publish. Report this and end the task:

> No Comfy Registry token is configured, so I'm not publishing. Create an API key at
> <https://registry.comfy.org> (publisher page → API Keys), then set it as an environment
> variable or add it to `.env` in the node pack root:
>
> ```
> REGISTRY_ACCESS_TOKEN=<your key>
> ```
>
> If you use `.env`, add `.env` to `.gitignore` first.

### Loading it

`scripts/load_token.sh` in this skill does the resolution: environment → `.env` → exit 1
with that message. It sets `$TOKEN`, prints only the source and character count, and warns
when `.env` is not gitignored.

**Shell state does not survive between tool calls**, so a token loaded in one call is gone
by the next. Source the loader and run the publish in a **single** Bash invocation:

```bash
. "$SKILL_DIR/scripts/load_token.sh"          # sets $TOKEN, or exits 1
uvx comfy-cli node publish --token "$TOKEN"
```

Substitute the real path to this skill's directory for `$SKILL_DIR`.

---

## Step 2 — Preflight the node pack

Run from the node pack root (the directory holding `pyproject.toml`):

```bash
uv run --no-project --python 3.11 "$SKILL_DIR/scripts/preflight.py"
```

Read-only, never touches the token. It checks:

- `pyproject.toml` exists and parses
- required fields: `project.name`, `project.version`, `project.urls.Repository`,
  `tool.comfy.PublisherId`
- `project.name` against registry naming rules; `project.version` is semver `X.Y.Z`
- **version collision** — queries `https://api.comfy.org/nodes/<name>` and fails when the
  local version is already published or is behind the published one
- **git state** — repo present, untracked files that will be excluded, uncommitted changes
- **secret leak guard** — see below

Exit code 1 means do not publish. If the script is unavailable, do the checks by hand; do
not skip the version collision or the leak guard.

### The secret leak guard (do not skip)

`comfy node publish` builds the archive from `git ls-files`. But when git is unavailable or
the directory is not a git repo it prints
`Warning: Not in a git repository or git not installed. Zipping all files.` and packages
**everything in the directory** — `.env`, keys, virtualenvs — then uploads that to the
public registry.

**Hard rule:** if the directory is not a git repository (or `git` is not on PATH) and any
of `.env`, `.env.*`, `*.pem`, `*.key`, or a credentials file exists, refuse to publish and
explain why. Fix the git repo, or move the secret out of the directory, first.

Equally: a `.env` that is *git-tracked* gets uploaded even in a healthy repo. Untrack it
(`git rm --cached .env`) before publishing.

### What actually gets uploaded

- Contents come from **git-tracked paths** (`git ls-files`), read from the **working tree** —
  so uncommitted edits to tracked files do ship.
- **Untracked files are silently omitted.** A brand-new file is missing from the published
  version unless it was `git add`ed.
- `.comfyignore` patterns are excluded on top of that.
- `[tool.comfy] includes = ['dist']` force-includes otherwise-gitignored build output.

So `git add` everything the release needs, and confirm the file list before publishing.

---

## Step 3 — Validate

```bash
uvx comfy-cli --skip-prompt --no-enable-telemetry env >/dev/null
uvx comfy-cli node validate
```

The first line seeds comfy-cli's config so the first-run telemetry prompt cannot block a
non-interactive run — it mirrors what the official GitHub Action does. Drop
`--no-enable-telemetry` if the user wants telemetry on.

`validate` runs exactly the checks publish runs: a non-empty `project.version`, then
`ruff check --select S102,S307,E702` (`exec`, `eval`, multiple statements on one line).
Ruff findings are **warnings today and are documented to become errors** — report them, and
fix them if the user asks. It also warns when `project.license` is absent or malformed;
the accepted forms are `{ file = "LICENSE" }` and `{ text = "MIT License" }`.

`ruff` ships as a comfy-cli dependency, so `uvx` always has it. `Ruff is not installed`
only appears with a pip-installed comfy-cli in an environment missing it.

To inspect the exact archive without publishing:

```bash
uvx comfy-cli node pack && unzip -l node.zip | head -50
rm -f node.zip
```

---

## Step 4 — Confirm, then publish

Publishing is irreversible and public. **Get explicit confirmation from the user first**,
showing the concrete facts:

- the `name` and `PublisherId` it publishes under
- the version going out, and the version currently on the registry
- how many files are in the archive, and any untracked files being **excluded**

Then publish — loader and command in one Bash call:

```bash
. "$SKILL_DIR/scripts/load_token.sh"
uvx comfy-cli --skip-prompt --no-enable-telemetry env >/dev/null
uvx comfy-cli node publish --token "$TOKEN"
```

`$TOKEN` stays a variable reference in the command text; the secret is never rendered.

### Adding a changelog

`--changelog` fills the registry's Updates section. It is plain text, not a secret:

```bash
uvx comfy-cli node publish --token "$TOKEN" --changelog "Fix mask dtype on the CPU backend"
uvx comfy-cli node publish --token "$TOKEN" --changelog-file CHANGELOG_LATEST.md
```

`--changelog` and `--changelog-file` are mutually exclusive; `COMFY_NODE_CHANGELOG` is
honored as an env var. `--changelog-file -` reads stdin, which makes `--token` mandatory
(the key prompt cannot share stdin) — the flow above already satisfies that.

Expected output on success:

```
Validating node configuration...
Running security checks...
✓ All validation checks passed successfully
Publishing node version...
Creating zip file...
Uploading zip file...
```

Confirm it went live:

```bash
curl -s https://api.comfy.org/nodes/<node-name> \
  | python -c "import sys,json;print(json.load(sys.stdin)['latest_version']['version'])"
```

---

## `pyproject.toml` reference

```toml
[project]
name = "my-comfy-nodes"          # required; permanent registry id, case-insensitive, <100 chars
version = "1.0.1"                # required; semver X.Y.Z; must be new on every publish
description = "What the pack does"
license = { file = "LICENSE" }   # or { text = "MIT License" }
requires-python = ">=3.10"
dependencies = []
classifiers = ["Operating System :: OS Independent"]

[project.urls]
Repository = "https://github.com/user/my-comfy-nodes"   # required

[tool.comfy]
PublisherId = "your-publisher-id"   # required; from your registry.comfy.org publisher page
DisplayName = "My Comfy Nodes"      # changeable later, unlike name
Icon = "https://.../icon.png"       # <=400x400, square
Banner = "https://.../banner.png"   # 21:9
requires-comfyui = ">=1.0.0"
includes = []                       # force-include gitignored dirs, e.g. ['dist']
```

`comfy node init` scaffolds this file when the pack has none; it refuses to overwrite an
existing `pyproject.toml`.

`project.name` is **permanent** — it is the registry identifier and cannot be changed after
the first publish. Get it right before the first release; only `DisplayName` is editable later.

---

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `Failed to validate token` / 401 | Key is wrong, revoked, or belongs to another publisher. Regenerate at registry.comfy.org and update the env var or `.env`. |
| Version rejected / already exists | The registry never accepts a duplicate version. Bump `project.version` and publish again. |
| `Error: project version is empty` | Set `project.version`, or set `[tool.comfy.version].path` if using `dynamic = ["version"]`. |
| `Ruff is not installed` | Only with a pip-installed comfy-cli; `pip install ruff`, or use `uvx comfy-cli`, which bundles it. |
| `Warning: Not in a git repository ... Zipping all files.` | **Stop.** Every file in the directory, `.env` included, would be uploaded. Fix git first. |
| Published version is missing new files | They were untracked. `git add` them and publish a new version — the bad one cannot be replaced. |
| Command hangs with no output | It is waiting on the API-key prompt or the first-run telemetry prompt. Pass `--token` and run the `--skip-prompt` seed line. |
| PublisherId mismatch | The token's publisher must match `[tool.comfy] PublisherId`. |

---

## Publishing from GitHub Actions instead

For release-on-version-bump, use the official action. The token lives in repository
secrets and never enters the repo:

```yaml
# .github/workflows/publish_action.yml
name: Publish to Comfy Registry
on:
  push:
    branches: [main]
    paths: [pyproject.toml]      # fires only when the version file changes
permissions:
  contents: read
jobs:
  publish-node:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: Comfy-Org/publish-node-action@main
        with:
          personal_access_token: ${{ secrets.REGISTRY_ACCESS_TOKEN }}
```

Add the key under **Settings → Secrets and variables → Actions** as
`REGISTRY_ACCESS_TOKEN`. Never inline it in the workflow file, and never run this job on
`pull_request_target` — a fork PR could exfiltrate the secret.

Under the hood the action runs exactly:

```bash
comfy --skip-prompt --no-enable-telemetry env
comfy node publish --token ${{ inputs.personal_access_token }}
```

---

## If the token was exposed

If a token was ever echoed into a log, transcript, commit, or shared file, treat it as
compromised: revoke it at registry.comfy.org, generate a new one, and update every place
that stores it — local environment, `.env`, GitHub secrets, CI. Rotating is cheap; a
leaked publish key is not.
