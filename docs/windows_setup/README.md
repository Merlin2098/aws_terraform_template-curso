# Windows Setup

This guide prepares a Windows machine to use this template and to install it into
another repository.

## Prepare the Template Repository

From the repository root:

```powershell
.\scripts\windows\setup_env.ps1
```

This Windows wrapper resolves Python automatically, creates `.venv` if needed
with `python -m venv`, and installs dependencies with `pip` from the project's
current `requirements.txt` (and `requirements-dev.txt` unless `-NoDev` is
passed).

When you install this template into another repository, the installer copies
`requirements.txt` and `requirements-dev.txt`.

Install pre-commit into the current repository environment:

```powershell
.\.venv\Scripts\pre-commit.exe install
.\.venv\Scripts\pre-commit.exe --version
```

To run all configured hooks manually:

```powershell
.\.venv\Scripts\pre-commit.exe run --all-files
```

Reference: https://pre-commit.com/

## Refresh or Change the Environment

To refresh the local environment after editing dependencies:

```powershell
.\scripts\windows\update_venv.ps1
```

To sync only runtime dependencies (skip development tooling):

```powershell
.\scripts\windows\setup_env.ps1 -NoDev
.\scripts\windows\update_venv.ps1 -NoDev
```

## Install This Template Into Another Repo

Preview the install without writing files:

```powershell
.\.venv\Scripts\python.exe install_windows.py --dry-run --target C:\path\to\target-repo
```

Install the template by selecting the target repository folder in Explorer:

```powershell
.\.venv\Scripts\python.exe install_windows.py
```

Install the template with an explicit target path:

```powershell
.\.venv\Scripts\python.exe install_windows.py --target C:\path\to\target-repo
```

Overwrite existing target files only when intentional:

```powershell
.\.venv\Scripts\python.exe install_windows.py --target C:\path\to\target-repo --force
```

If the target repository already has a `.gitignore`, the installer keeps that
file and appends only the ignore rules that are present in the template
`.gitignore` but missing in the host. If the target repository does not have a
`.gitignore`, the template `.gitignore` is copied as-is.

The installer does not run Terraform, install dependencies, initialize Git, or
execute pre-commit in the target repository.

The installer also leaves the installer entrypoints and template docs behind:
`install_windows.py`, `install_linux.py`, files named `README.md`, and `docs/`
are not copied to the target repository.

## How the Host Setup Works

The installer:

- copies `requirements.txt` and `requirements-dev.txt`
- writes `.framework-version.json` to track the installed template version

Packaging bundles the runtime `requirements.txt` alongside `src/` for
deployment.
