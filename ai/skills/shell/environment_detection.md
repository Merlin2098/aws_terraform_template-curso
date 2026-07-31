# Environment Detection

## When to use

- Before generating any shell script — Git Bash is the default target
- When the target platform is ambiguous (Windows native, WSL, Git Bash, Linux)
- When deciding whether a task actually requires PowerShell (Windows Services/Registry/Scheduled Tasks) instead of Bash
- When the user hasn't specified the runtime environment

## Detection approach

Always determine the environment before writing a single line of script. Ask or detect:

| Signal | How to detect |
|---|---|
| OS family | `uname -s` (Bash) |
| Git Bash | `$MSYSTEM` is set (e.g. `MINGW64`) |
| WSL | `uname -r` contains `microsoft` or `WSL` |
| macOS | `uname -s` = `Darwin` |
| Shell type (if PowerShell is genuinely required) | `$PSVersionTable` present → PowerShell |
| PowerShell version (only if PowerShell is required) | `$PSVersionTable.PSVersion.Major` — 5 = Windows PS, 7+ = PS Core |

## Expected output (document in script header)

```yaml
environment:
  os: windows          # windows | linux | macos
  shell: bash          # bash | powershell
  git_bash: true
  wsl_enabled: false   # true | false | unknown
  shell_version: null  # only relevant when shell: powershell
```

## Bash detection snippet (default)

```bash
#!/usr/bin/env bash
IS_WSL=false
if grep -qi microsoft /proc/version 2>/dev/null; then IS_WSL=true; fi
IS_GIT_BASH=false
if [[ -n "${MSYSTEM:-}" ]]; then IS_GIT_BASH=true; fi
```

## PowerShell detection snippet (only when PowerShell is required)

```powershell
$isPS7Plus = $PSVersionTable.PSVersion.Major -ge 7
$isWSL     = (Get-Item WSL:\ -ErrorAction SilentlyContinue) -ne $null
```

## Best practices

- Default to Bash (Git Bash on Windows, native Bash on Linux/macOS/WSL) — it
  runs unchanged across every environment this project targets
- Only generate a PowerShell script when the task is Windows-native
  administration with no Bash equivalent (services, registry, scheduled
  tasks — see `ai/skills/shell/powershell_windows_admin.md`) or the user
  explicitly asks for PowerShell
- Prefer `#!/usr/bin/env bash` (portable) over `/bin/bash` (absolute path)
- When a PowerShell script is genuinely required, prefer `pwsh` (PS 7+) over
  `powershell.exe` (PS 5.1) for cross-platform reach; call out when PS
  5.1-only cmdlets are needed

## Avoid

- Defaulting to PowerShell when Bash would run identically across environments
- Writing platform-specific scripts without documenting the target environment in the header
- Hardcoding `C:\` paths in scripts intended for Linux/WSL/Git Bash
- Assuming Git Bash isn't available on Windows — confirm via `$MSYSTEM` rather than reaching for PowerShell by default
- Combining OS-detection logic with business logic in the same function
