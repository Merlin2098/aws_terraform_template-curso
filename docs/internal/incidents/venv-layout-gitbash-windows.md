# Incident: `.venv` layout mismatch in Git Bash on Windows

**Status:** Resolved
**Introduced:** 2026-07-30
**Fixed:** 2026-07-30

---

## Problem

Running `scripts/python/update_venv.sh` from Git Bash failed with:

```
$ bash scripts/python/update_venv.sh
Starting virtual environment update from requirements files.

=== Phase 1: Validate Environment ===
[venv] Using existing interpreter: /c/Users/User/Documents/VS Code/aws_terraform_template/.venv/bin/python
scripts/python/update_venv.sh: line 76: /c/Users/User/Documents/VS Code/aws_terraform_template/.venv/bin/python: No such file or directory
```

## Root cause

`scripts/python/setup_env.sh` and `scripts/python/update_venv.sh` hardcoded the
POSIX venv layout (`.venv/bin/python`). On Windows, `python -m venv` always
produces a `Scripts/` layout (`.venv/Scripts/python.exe`) — that layout is
determined by the Python interpreter and OS, not by the shell used to invoke
it. Running the same command from Git Bash instead of PowerShell/cmd does
**not** change the layout: a Windows Python interpreter always creates
`Scripts/`, never `bin/`.

Since Git Bash is the standard terminal for this project, the scripts needed
to work against a Windows-created `.venv` without requiring it to be
recreated.

## Fix

Both scripts now resolve the venv interpreter with a small helper that checks
both layouts:

```bash
resolve_venv_python() {
    local venv_dir="$1"
    if [[ -x "${venv_dir}/bin/python" ]]; then
        printf '%s\n' "${venv_dir}/bin/python"
    elif [[ -x "${venv_dir}/Scripts/python.exe" ]]; then
        printf '%s\n' "${venv_dir}/Scripts/python.exe"
    else
        printf "No python interpreter found under '%s' (checked bin/python and Scripts/python.exe).\n" "${venv_dir}" >&2
        exit 1
    fi
}
```

See `scripts/python/setup_env.sh` and `scripts/python/update_venv.sh`.

## Takeaway

Don't assume a POSIX venv layout just because the invoking shell is Git Bash.
On Windows the interpreter still writes to `Scripts/`, not `bin/`. Any script
under `scripts/python/` that locates the venv interpreter must check both
paths.
