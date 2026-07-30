# Linux Setup

This guide prepares an Ubuntu-like Linux machine to use this template and to
install it into another repository.

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

Install pre-commit into the current repository environment:

```bash
./.venv/bin/pre-commit install
./.venv/bin/pre-commit --version
```

To run all configured hooks manually:

```bash
./.venv/bin/pre-commit run --all-files
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
