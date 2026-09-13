<#
.SYNOPSIS
    PowerShell equivalent of scripts/python/update_venv.sh for students without Git Bash.

.DESCRIPTION
    Upgrades dependencies in an existing .venv from requirements.txt (and, by
    default, requirements-dev.txt). Mirrors update_venv.sh phase for phase.

.PARAMETER IncludeDev
    Install requirements-dev.txt explicitly (default behavior).

.PARAMETER NoDev
    Skip requirements-dev.txt.

.EXAMPLE
    .\scripts\python\update_venv.ps1

.EXAMPLE
    .\scripts\python\update_venv.ps1 -NoDev
#>
[CmdletBinding()]
param(
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

$venvDir = Join-Path $repoRoot ".venv"
if (-not (Test-Path $venvDir)) {
    Write-Error "No .venv directory was found. Run .\scripts\python\setup_env.ps1 first."
    exit 1
}
$venvPython = Resolve-VenvPython $venvDir

Write-Step "Starting virtual environment update from requirements files."

Write-Phase "Phase 1: Validate Environment"
Write-Step "[venv] Using existing interpreter: $venvPython"
& $venvPython --version

$requirementsPath = Join-Path $repoRoot "requirements.txt"
if (-not (Test-Path $requirementsPath)) {
    Write-Error "requirements.txt is required for the pip update flow."
    exit 1
}
Write-Step "[Project] Verified requirements.txt and existing .venv."

Write-Phase "Phase 2: Update Dependencies"
& $venvPython -m pip install --upgrade pip

$installArgs = @("-m", "pip", "install", "--upgrade", "-r", "requirements.txt")
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

Write-Phase "Phase 3: Summary"
Write-Step "Virtual environment updated successfully."
Write-Host "Suggested interpreter path: $venvPython"
