<#
.SYNOPSIS
    PowerShell equivalent of scripts/python/setup_env.sh for students without Git Bash.

.DESCRIPTION
    Creates (or reuses) .venv and installs requirements.txt (and, by default,
    requirements-dev.txt) with pip. Mirrors setup_env.sh phase for phase.

.PARAMETER PythonPath
    Use this Python interpreter explicitly instead of resolving one from PATH.

.PARAMETER IncludeDev
    Install requirements-dev.txt explicitly (default behavior).

.PARAMETER NoDev
    Skip requirements-dev.txt.

.EXAMPLE
    .\scripts\python\setup_env.ps1

.EXAMPLE
    .\scripts\python\setup_env.ps1 -NoDev
#>
[CmdletBinding()]
param(
    [string]$PythonPath,
    [switch]$IncludeDev,
    [switch]$NoDev
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($IncludeDev -and $NoDev) {
    Write-Error "Use either -IncludeDev or -NoDev, but not both."
    exit 1
}
$useDevDependencies = -not $NoDev

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..\..")

function Write-Step {
    param([string]$Message)
    Write-Host $Message
}

function Write-Phase {
    param([string]$Title)
    Write-Host ""
    Write-Host "=== $Title ==="
}

function Resolve-PythonCommand {
    if ($PythonPath) {
        if (-not (Test-Path $PythonPath)) {
            Write-Error "Python not found at '$PythonPath'."
            exit 1
        }
        & $PythonPath --version *> $null
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Python at '$PythonPath' did not respond correctly."
            exit 1
        }
        return $PythonPath
    }

    foreach ($candidate in @("python", "py")) {
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($command) {
            & $candidate --version *> $null
            if ($LASTEXITCODE -eq 0) {
                return $candidate
            }
        }
    }

    Write-Error "Unable to resolve a working Python interpreter. Tried: python, py."
    exit 1
}

function Resolve-VenvPython {
    param([string]$VenvDir)
    $winPython = Join-Path $VenvDir "Scripts\python.exe"
    $posixPython = Join-Path $VenvDir "bin/python"
    if (Test-Path $winPython) {
        return $winPython
    }
    elseif (Test-Path $posixPython) {
        return $posixPython
    }
    else {
        Write-Error "No python interpreter found under '$VenvDir' (checked Scripts\python.exe and bin/python)."
        exit 1
    }
}

$selectedPython = Resolve-PythonCommand

Write-Step "Starting pip environment setup for this repository."

Write-Phase "Phase 1: Resolve Python"
Write-Step "[Python] Using interpreter: $selectedPython"
& $selectedPython --version

Write-Phase "Phase 2: Create Virtual Environment"
$venvDir = Join-Path $repoRoot ".venv"
if (-not (Test-Path $venvDir)) {
    Write-Step "[venv] Creating .venv with $selectedPython -m venv"
    & $selectedPython -m venv $venvDir
}
else {
    Write-Step "[venv] Reusing existing .venv"
}
$venvPython = Resolve-VenvPython $venvDir

Write-Phase "Phase 3: Install Dependencies"
$requirementsPath = Join-Path $repoRoot "requirements.txt"
if (-not (Test-Path $requirementsPath)) {
    Write-Error "requirements.txt is required for the pip setup flow."
    exit 1
}

& $venvPython -m pip install --upgrade pip

$installArgs = @("-m", "pip", "install", "-r", "requirements.txt")
$devRequirementsPath = Join-Path $repoRoot "requirements-dev.txt"
if ($useDevDependencies -and (Test-Path $devRequirementsPath)) {
    $installArgs += @("-r", "requirements-dev.txt")
}
Write-Step "[Dependencies] Running: $venvPython $($installArgs -join ' ')"

Push-Location $repoRoot
try {
    & $venvPython @installArgs
}
finally {
    Pop-Location
}

Write-Phase "Phase 4: Summary"
Write-Step "Environment setup completed successfully."
Write-Host "Suggested interpreter path: $venvPython"
