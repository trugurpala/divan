[CmdletBinding()]
param([string]$Python)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$candidates = @()
if ($Python) {
    $candidates += @{ Executable = $Python; Prefix = @() }
} else {
    $candidates += @{ Executable = 'python'; Prefix = @() }
    $candidates += @{ Executable = 'python3'; Prefix = @() }
    $candidates += @{ Executable = 'py'; Prefix = @('-3') }
    if ($env:USERPROFILE) {
        $bundledPython = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
        $candidates += @{ Executable = $bundledPython; Prefix = @() }
    }
}

$interpreter = $null
foreach ($candidate in $candidates) {
    if (-not (Get-Command $candidate.Executable -ErrorAction SilentlyContinue)) { continue }
    try {
        $prefix = $candidate.Prefix
        & $candidate.Executable @prefix -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)' 2>$null
        if ($LASTEXITCODE -eq 0) {
            $interpreter = $candidate
            break
        }
    } catch { continue }
}
if (-not $interpreter) {
    throw 'Python 3.12+ was not found. Supply -Python with an existing interpreter; no packages were installed.'
}

function Invoke-PythonGate([string[]]$Arguments) {
    $prefix = $interpreter.Prefix
    & $interpreter.Executable @prefix @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Python verification failed (exit $LASTEXITCODE): $($Arguments -join ' ')" }
}

Push-Location $repoRoot
try {
    Invoke-PythonGate -Arguments @('--version')
    Invoke-PythonGate -Arguments @('scripts/divan_v2_validate.py')
    Invoke-PythonGate -Arguments @('-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_*.py', '-v')
    Invoke-PythonGate -Arguments @('scripts/package_divan_v2.py')
    & git diff --check
    if ($LASTEXITCODE -ne 0) { throw 'Git whitespace verification failed.' }
    Write-Output 'Divan verification: PASS'
} finally {
    Pop-Location
}
