param(
    [string]$PythonPath,
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

function Assert-PythonPath {
    param(
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Python not found at '$Path'."
    }
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

function Test-CommandSpec {
    param(
        [pscustomobject]$CommandSpec
    )

    $hasNativePreference = Test-Path Variable:\PSNativeCommandUseErrorActionPreference
    if ($hasNativePreference) {
        $previousNativePreference = $PSNativeCommandUseErrorActionPreference
        $PSNativeCommandUseErrorActionPreference = $false
    }

    try {
        & $CommandSpec.Command @($CommandSpec.BaseArguments + @("--version")) *> $null
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
    finally {
        if ($hasNativePreference) {
            $PSNativeCommandUseErrorActionPreference = $previousNativePreference
        }
    }
}

function Resolve-PythonCommand {
    param(
        [string]$ExplicitPythonPath
    )

    $attemptedResolvers = @()

    if ($ExplicitPythonPath) {
        $attemptedResolvers += "explicit path '$ExplicitPythonPath'"
        Assert-PythonPath -Path $ExplicitPythonPath
        $pythonCommand = New-CommandSpec -Command $ExplicitPythonPath -BaseArguments @() -Description "explicit path '$ExplicitPythonPath'"
        if (-not (Test-CommandSpec -CommandSpec $pythonCommand)) {
            throw "Python at '$ExplicitPythonPath' did not respond correctly."
        }
        return $pythonCommand
    }

    $candidates = @(
        (New-CommandSpec -Command "py" -BaseArguments @("-3") -Description "py -3"),
        (New-CommandSpec -Command "python" -BaseArguments @() -Description "python from PATH")
    )

    foreach ($candidate in $candidates) {
        $attemptedResolvers += $candidate.Description
        if (Test-CommandSpec -CommandSpec $candidate) {
            return $candidate
        }
    }

    $attemptedText = $attemptedResolvers -join ", "
    throw "Unable to resolve a working Python interpreter. Tried: $attemptedText. Install/configure Python or pass -PythonPath."
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

function Assert-RequirementsExists {
    if (-not (Test-Path -LiteralPath "requirements.txt")) {
        throw "requirements.txt is required for the pip setup flow."
    }
}

function Ensure-Venv {
    param(
        [pscustomobject]$PythonCommand
    )

    if (Test-Path -LiteralPath ".venv") {
        Write-Step "[Environment] Reusing existing virtual environment at .venv" ([ConsoleColor]::DarkYellow)
        return
    }

    Write-Step "[Environment] Creating virtual environment with python -m venv..." ([ConsoleColor]::Yellow)
    Invoke-CommandSpec -CommandSpec $PythonCommand -Arguments @("-m", "venv", ".venv")
}

Write-Step "Starting pip environment setup for this repository." ([ConsoleColor]::Cyan)

Write-Phase "Phase 1: Resolve Python"
$pythonCommand = Resolve-PythonCommand -ExplicitPythonPath $PythonPath
Write-Step "[Python] Using interpreter resolved via $($pythonCommand.Description)." ([ConsoleColor]::DarkCyan)

Write-Step "[Python] Validating the selected Python interpreter..." ([ConsoleColor]::Yellow)
Invoke-CommandSpec -CommandSpec $pythonCommand -Arguments @("--version")

Write-Phase "Phase 2: Validate Project"
Write-Step "[Project] Verifying that requirements.txt is available..." ([ConsoleColor]::Yellow)
Assert-RequirementsExists

Write-Phase "Phase 3: Prepare Environment"
Ensure-Venv -PythonCommand $pythonCommand

$venvPython = Join-Path (Get-Location) ".venv\Scripts\python.exe"
$venvCommand = New-CommandSpec -Command $venvPython -BaseArguments @() -Description "virtual environment interpreter"

Write-Phase "Phase 4: Install Dependencies"
Invoke-CommandSpec -CommandSpec $venvCommand -Arguments @("-m", "pip", "install", "--upgrade", "pip")

$installArguments = @("-m", "pip", "install", "-r", "requirements.txt")
if ($useDevDependencies -and (Test-Path -LiteralPath "requirements-dev.txt")) {
    $installArguments += @("-r", "requirements-dev.txt")
}
$dependencyMode = if ($useDevDependencies) { "including dev dependencies" } else { "without dev dependencies" }
Write-Step "[Dependencies] Installing requirements ($dependencyMode)..." ([ConsoleColor]::Yellow)
Invoke-CommandSpec -CommandSpec $venvCommand -Arguments $installArguments

Write-Phase "Phase 5: Summary"
Write-Step "Environment setup completed successfully." ([ConsoleColor]::Green)
Write-Host "Dev dependencies enabled: $useDevDependencies"
Write-Host "Virtual environment path: .venv"
Write-Host "VS Code interpreter selection remains a manual step."
Write-Host "Suggested interpreter path: $venvPython"
