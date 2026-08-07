param(
    [Parameter(Mandatory = $true)]
    [string]$AppExe,

    [Parameter(Mandatory = $true)]
    [string]$CoreExe,

    [string]$Output
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Invoke-DivanCore {
    param([hashtable]$Request)

    $requestJson = $Request | ConvertTo-Json -Compress -Depth 20
    $lines = @($requestJson | & $CoreExe)
    $exitCode = $LASTEXITCODE
    $text = ($lines -join "`n").Trim()
    if ($exitCode -ne 0) {
        throw "Installed Divan Core request failed with exit code ${exitCode}: $text"
    }
    if (-not $text) {
        throw "Installed Divan Core returned no JSON"
    }
    $response = $text | ConvertFrom-Json
    if (-not $response.ok) {
        throw "Installed Divan Core returned an error: $text"
    }
    return $response.result
}

function Invoke-DesktopRestart {
    param([int]$Attempt)

    $process = Start-Process -FilePath $AppExe -PassThru
    try {
        Start-Sleep -Seconds 4
        if ($process.HasExited) {
            throw "Installed Divan.exe exited during lifecycle restart attempt $Attempt with code $($process.ExitCode)"
        }
    }
    finally {
        if (-not $process.HasExited) {
            Stop-Process -Id $process.Id -Force
            Wait-Process -Id $process.Id -ErrorAction SilentlyContinue
        }
    }
}

function Get-Tool {
    param(
        [object]$Readiness,
        [string]$Id
    )

    return @($Readiness.tools | Where-Object { $_.id -eq $Id }) | Select-Object -First 1
}

if (-not (Test-Path $AppExe -PathType Leaf)) {
    throw "Installed Divan.exe does not exist: $AppExe"
}
if (-not (Test-Path $CoreExe -PathType Leaf)) {
    throw "Installed Divan Core does not exist: $CoreExe"
}

$root = Join-Path $env:RUNNER_TEMP "divan-desktop-lifecycle-$PID"
$stateRoot = Join-Path $root "state"
$projectRoot = Join-Path $root "project"
$probeRoot = Join-Path $root "probe-profile"
$fakeBin = Join-Path $root "fake-bin"
New-Item -ItemType Directory -Path $stateRoot, $projectRoot, $probeRoot, $fakeBin -Force | Out-Null

$previousDataDir = $env:DIVAN_DATA_DIR
$previousPath = $env:PATH
$previousAppData = $env:APPDATA
$previousLocalAppData = $env:LOCALAPPDATA
$previousUserProfile = $env:USERPROFILE

try {
    $env:DIVAN_DATA_DIR = $stateRoot

    & git init $projectRoot | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Could not create lifecycle Git repository"
    }

    $project = Invoke-DivanCore @{ command = "project.register"; root = $projectRoot }
    $task = Invoke-DivanCore @{
        command = "task.create"
        task_id = "DIV-LIFECYCLE"
        title = "Persist Core state across Desktop restart"
        project_id = $project.project_id
    }
    $planned = Invoke-DivanCore @{ command = "task.plan"; task_id = $task.task_id }
    if ($planned.state -ne "planned" -or $null -ne $planned.mandate_id) {
        throw "Lifecycle fixture did not enter authority-neutral planned state"
    }

    Invoke-DesktopRestart -Attempt 1
    $afterFirstTasks = @(Invoke-DivanCore @{ command = "task.list" })
    $afterFirstProjects = @(Invoke-DivanCore @{ command = "project.list" })
    $afterFirst = $afterFirstTasks | Where-Object { $_.task_id -eq "DIV-LIFECYCLE" } | Select-Object -First 1
    if (-not $afterFirst -or $afterFirst.state -ne "planned" -or $null -ne $afterFirst.mandate_id) {
        throw "Core task state did not survive the first Desktop process restart exactly"
    }
    if (-not ($afterFirstProjects | Where-Object { $_.project_id -eq $project.project_id })) {
        throw "Core project registry did not survive the first Desktop process restart"
    }

    Invoke-DesktopRestart -Attempt 2
    $afterSecondTasks = @(Invoke-DivanCore @{ command = "task.list" })
    $afterSecond = $afterSecondTasks | Where-Object { $_.task_id -eq "DIV-LIFECYCLE" } | Select-Object -First 1
    if (-not $afterSecond -or $afterSecond.state -ne "planned" -or $null -ne $afterSecond.mandate_id) {
        throw "Desktop restart reconstructed task authority or lost persisted Core state"
    }

    $existingOrca = Get-Command orca -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    $pathEntries = @($previousPath -split ";" | Where-Object { $_ })
    if ($existingOrca) {
        $existingOrcaDirectory = Split-Path -Parent $existingOrca.Source
        $pathEntries = @($pathEntries | Where-Object {
            -not [string]::Equals($_.TrimEnd("\"), $existingOrcaDirectory.TrimEnd("\"), [System.StringComparison]::OrdinalIgnoreCase)
        })
    }
    $git = Get-Command git -CommandType Application -ErrorAction Stop | Select-Object -First 1
    $gitDirectory = Split-Path -Parent $git.Source
    if (-not ($pathEntries | Where-Object {
        [string]::Equals($_.TrimEnd("\"), $gitDirectory.TrimEnd("\"), [System.StringComparison]::OrdinalIgnoreCase)
    })) {
        $pathEntries = @($gitDirectory) + $pathEntries
    }

    $emptyAppData = Join-Path $probeRoot "AppData-Roaming"
    $emptyLocalAppData = Join-Path $probeRoot "AppData-Local"
    $emptyUserProfile = Join-Path $probeRoot "User"
    New-Item -ItemType Directory -Path $emptyAppData, $emptyLocalAppData, $emptyUserProfile -Force | Out-Null
    $env:APPDATA = $emptyAppData
    $env:LOCALAPPDATA = $emptyLocalAppData
    $env:USERPROFILE = $emptyUserProfile
    $env:PATH = $pathEntries -join ";"

    $absent = Invoke-DivanCore @{ command = "readiness" }
    $absentOrca = Get-Tool -Readiness $absent -Id "orca"
    if (-not $absent.ready) {
        throw "Orca-absent first run lost required Git readiness"
    }
    if ($absentOrca.available -or (@($absent.engines) -contains "orca")) {
        throw "Orca-absent first run incorrectly advertised Orca"
    }

    $fakeOrca = Join-Path $fakeBin "orca.cmd"
    "@echo off`r`necho orca-lifecycle-test 1.0.0`r`n" | Set-Content -Path $fakeOrca -Encoding Ascii
    $env:PATH = "$fakeBin;$($env:PATH)"

    $present = Invoke-DivanCore @{ command = "readiness" }
    $presentOrca = Get-Tool -Readiness $present -Id "orca"
    $capabilities = Invoke-DivanCore @{ command = "capabilities" }
    if (-not $presentOrca.available -or -not (@($present.engines) -contains "orca")) {
        throw "Orca-present first run did not discover the replaceable Orca engine"
    }
    if ($capabilities.product -ne "Divan") {
        throw "Execution engine discovery changed Core product authority"
    }
    if (-not (@($capabilities.features) -contains "mandate-gate") -or -not (@($capabilities.features) -contains "approval-gate")) {
        throw "Orca-present first run bypassed Divan mandate/approval authority capabilities"
    }

    $evidence = [ordered]@{
        schema_version = 1
        status = "pass"
        desktop_process_restarts = 2
        persisted_task_state = $afterSecond.state
        persisted_task_has_mandate = ($null -ne $afterSecond.mandate_id)
        orca_absent_available = [bool]$absentOrca.available
        orca_absent_engine_registered = [bool](@($absent.engines) -contains "orca")
        orca_present_available = [bool]$presentOrca.available
        orca_present_engine_registered = [bool](@($present.engines) -contains "orca")
        authority_product = $capabilities.product
        mandate_gate = [bool](@($capabilities.features) -contains "mandate-gate")
        approval_gate = [bool](@($capabilities.features) -contains "approval-gate")
    }
    $json = $evidence | ConvertTo-Json -Depth 10
    if ($Output) {
        $outputParent = Split-Path -Parent $Output
        if ($outputParent) {
            New-Item -ItemType Directory -Path $outputParent -Force | Out-Null
        }
        $json | Set-Content -Path $Output -Encoding utf8
    }
    Write-Output $json
}
finally {
    $env:DIVAN_DATA_DIR = $previousDataDir
    $env:PATH = $previousPath
    $env:APPDATA = $previousAppData
    $env:LOCALAPPDATA = $previousLocalAppData
    $env:USERPROFILE = $previousUserProfile
}
