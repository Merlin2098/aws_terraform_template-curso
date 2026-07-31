# Linux Setup

This guide prepares an Ubuntu-like Linux machine, or Git Bash on Windows, to
use this template and to install it into another repository.

## Prepare the Template Repository

From the repository root:

```bash
./scripts/python/setup_env.sh
```

This Git Bash wrapper resolves Python automatically, creates `.venv` with
`python -m venv`, and installs dependencies with `pip`.

By default, the setup installs:

- the runtime dependencies from `requirements.txt`
- the development dependencies from `requirements-dev.txt`

> **Note:** on Windows, `python -m venv` always creates a `Scripts/` layout
> (`.venv/Scripts/python.exe`), even when the command runs inside Git Bash —
> the layout follows the OS/interpreter, not the shell. On Linux/macOS it
> creates `.venv/bin/`. `scripts/python/setup_env.sh` and
> `scripts/python/update_venv.sh` detect whichever layout is present, so the
> same commands work unmodified on both. See
> `docs/incidents/venv-layout-gitbash-windows.md` for the incident this
> guarded against.

Install pre-commit into the current repository environment:

```bash
./.venv/bin/pre-commit install    # Linux/macOS
./.venv/Scripts/pre-commit.exe install    # Windows (Git Bash)
```

To run all configured hooks manually:

```bash
./.venv/bin/pre-commit run --all-files    # Linux/macOS
./.venv/Scripts/pre-commit.exe run --all-files    # Windows (Git Bash)
```

## Refresh or Change the Environment

To refresh the local environment after editing dependencies:

```bash
./scripts/python/update_venv.sh
```

To sync only runtime dependencies (skip development tooling):

```bash
./scripts/python/setup_env.sh --no-dev
./scripts/python/update_venv.sh --no-dev
```

## Install This Template Into Another Repo

Preview the install without writing files:

```bash
python3 install_linux.py --dry-run --target /path/to/target-repo
```

Install the template with an explicit target path:

```bash
python3 install_linux.py --target /path/to/target-repo
```

Overwrite existing target files only when intentional:

```bash
python3 install_linux.py --target /path/to/target-repo --force
```

`install_linux.py` copies the template into a host repository. It does not
bootstrap the current repository environment; use `./scripts/python/setup_env.sh`
for that.
