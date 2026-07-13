param(
    [switch]$IncludeDev,
    [switch]$NoDev
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if ($IncludeDev -and $NoDev) {
    throw "Use either -IncludeDev or -NoDev, but not both."
}

$useDevDependencies = $true
if ($NoDev) {
    $useDevDependencies = $false
}

function Write-Step {
    param(
        [string]$Message,
        [ConsoleColor]$Color = [ConsoleColor]::Yellow
    )

    Write-Host $Message -ForegroundColor $Color
}

function Write-Phase {
    param(
        [string]$Title
    )

    Write-Host ""
    Write-Host "=== $Title ===" -ForegroundColor Cyan
}

function New-CommandSpec {
    param(
        [string]$Command,
        [string[]]$BaseArguments,
        [string]$Description
    )

    return [pscustomobject]@{
        Command       = $Command
        BaseArguments = $BaseArguments
        Description   = $Description
    }
}

function Invoke-CommandSpec {
    param(
        [pscustomobject]$CommandSpec,
        [string[]]$Arguments
    )

    $allArguments = @($CommandSpec.BaseArguments + $Arguments)
    & $CommandSpec.Command @allArguments
    if ($LASTEXITCODE -ne 0) {
        $joinedArguments = $allArguments -join " "
        throw "Command failed: $($CommandSpec.Command) $joinedArguments"
    }
}

function Assert-ProjectState {
    if (-not (Test-Path -LiteralPath "requirements.txt")) {
        throw "requirements.txt is required for the pip update flow."
    }

    if (-not (Test-Path -LiteralPath ".venv")) {
        throw "No .venv directory was found. Run .\scripts\windows\setup_env.ps1 first."
    }
}

Write-Step "Starting virtual environment update from requirements files." ([ConsoleColor]::Cyan)

Write-Phase "Phase 1: Validate Environment"
Write-Step "[Project] Verifying project state and existing virtual environment..." ([ConsoleColor]::Yellow)
Assert-ProjectState

$venvPython = Join-Path (Get-Location) ".venv\Scripts\python.exe"
$venvCommand = New-CommandSpec -Command $venvPython -BaseArguments @() -Description "virtual environment interpreter"
Invoke-CommandSpec -CommandSpec $venvCommand -Arguments @("--version")

Write-Phase "Phase 2: Update Dependencies"
Invoke-CommandSpec -CommandSpec $venvCommand -Arguments @("-m", "pip", "install", "--upgrade", "pip")

$installArguments = @("-m", "pip", "install", "--upgrade", "-r", "requirements.txt")
if ($useDevDependencies -and (Test-Path -LiteralPath "requirements-dev.txt")) {
    $installArguments += @("-r", "requirements-dev.txt")
}
$dependencyMode = if ($useDevDependencies) { "including dev dependencies" } else { "without dev dependencies" }
Write-Step "[Dependencies] Updating requirements ($dependencyMode)..." ([ConsoleColor]::Yellow)
Invoke-CommandSpec -CommandSpec $venvCommand -Arguments $installArguments

Write-Phase "Phase 3: Summary"
Write-Step "Virtual environment updated successfully." ([ConsoleColor]::Green)
Write-Host "Dev dependencies enabled: $useDevDependencies"
Write-Host "Virtual environment path: .venv"
Write-Host "Suggested interpreter path: $venvPython"
