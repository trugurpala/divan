param(
    [Parameter(Mandatory = $true)]
    [string]$AppExe,

    [Parameter(Mandatory = $true)]
    [string]$CoreExe,

    [string]$Output
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Invoke-OttomanCore {
    param([hashtable]$Request)

    $requestJson = $Request | ConvertTo-Json -Compress -Depth 20
    $lines = @($requestJson | & $CoreExe)
    $exitCode = $LASTEXITCODE
    $text = ($lines -join "`n").Trim()
    if ($exitCode -ne 0) {
        throw "Installed Ottoman Core request failed with exit code ${exitCode}: $text"
    }
    if (-not $text) {
        throw "Installed Ottoman Core returned no JSON"
    }
    $response = $text | ConvertFrom-Json
    if (-not $response.ok) {
        throw "Installed Ottoman Core returned an error: $text"
    }
    return $response.result
}

function Invoke-DesktopRestart {
    param([int]$Attempt)

    $process = Start-Process -FilePath $AppExe -PassThru
    try {
        Start-Sleep -Seconds 4
        if ($process.HasExited) {
            throw "Installed Ottoman.exe exited during lifecycle restart attempt $Attempt with code $($process.ExitCode)"
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

function Get-OptionalProperty {
    param(
        [object]$Object,
        [string]$Name
    )

    if ($null -eq $Object) {
        return $null
    }
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) {
        return $null
    }
    return $property.Value
}

function Stop-ProcessTree {
    param([System.Diagnostics.Process]$Process)

    if ($null -eq $Process -or $Process.HasExited) {
        return
    }
    & taskkill.exe /PID $Process.Id /T /F | Out-Null
    $taskkillExit = $LASTEXITCODE
    Wait-Process -Id $Process.Id -ErrorAction SilentlyContinue
    if ($taskkillExit -ne 0 -and -not $Process.HasExited) {
        throw "Could not terminate interrupted Core process tree $($Process.Id)"
    }
}

if (-not (Test-Path $AppExe -PathType Leaf)) {
    throw "Installed Ottoman.exe does not exist: $AppExe"
}
if (-not (Test-Path $CoreExe -PathType Leaf)) {
    throw "Installed Ottoman Core does not exist: $CoreExe"
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
$previousFakeAgentMarker = $env:DIVAN_FAKE_AGENT_MARKER
$interruptedCore = $null

try {
    $env:DIVAN_DATA_DIR = $stateRoot

    & git init $projectRoot | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Could not create lifecycle Git repository"
    }
    & git -C $projectRoot config user.email "divan-ci@invalid.local"
    & git -C $projectRoot config user.name "Ottoman CI"
    "# Ottoman lifecycle fixture" | Set-Content -Path (Join-Path $projectRoot "README.md") -Encoding utf8
    & git -C $projectRoot add README.md
    & git -C $projectRoot commit -m "test: seed lifecycle fixture" | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Could not create lifecycle Git fixture commit"
    }

    $project = Invoke-OttomanCore @{ command = "project.register"; root = $projectRoot }
    $task = Invoke-OttomanCore @{
        command = "task.create"
        task_id = "DIV-LIFECYCLE"
        title = "Persist Core state across Desktop restart"
        project_id = $project.project_id
    }
    $planned = Invoke-OttomanCore @{ command = "task.plan"; task_id = $task.task_id }
    if ($planned.state -ne "planned" -or $null -ne $planned.mandate_id) {
        throw "Lifecycle fixture did not enter authority-neutral planned state"
    }

    Invoke-DesktopRestart -Attempt 1
    $afterFirstTasks = @(Invoke-OttomanCore @{ command = "task.list" })
    $afterFirstProjects = @(Invoke-OttomanCore @{ command = "project.list" })
    $afterFirst = $afterFirstTasks | Where-Object { $_.task_id -eq "DIV-LIFECYCLE" } | Select-Object -First 1
    if (-not $afterFirst -or $afterFirst.state -ne "planned" -or $null -ne $afterFirst.mandate_id) {
        throw "Core task state did not survive the first Desktop process restart exactly"
    }
    if (-not ($afterFirstProjects | Where-Object { $_.project_id -eq $project.project_id })) {
        throw "Core project registry did not survive the first Desktop process restart"
    }

    Invoke-DesktopRestart -Attempt 2
    $afterSecondTasks = @(Invoke-OttomanCore @{ command = "task.list" })
    $afterSecond = $afterSecondTasks | Where-Object { $_.task_id -eq "DIV-LIFECYCLE" } | Select-Object -First 1
    if (-not $afterSecond -or $afterSecond.state -ne "planned" -or $null -ne $afterSecond.mandate_id) {
        throw "Desktop restart reconstructed task authority or lost persisted Core state"
    }

    # Prove a real process interruption cannot silently resume mutation. The fake
    # Codex binary is only a deterministic hanging worker; Ottoman still owns the
    # mandate, worktree creation, pending execution record and recovery decision.
    $fakeCodex = Join-Path $fakeBin "codex.cmd"
    $agentMarker = Join-Path $root "fake-codex-started.txt"
    @"
@echo off
> "%DIVAN_FAKE_AGENT_MARKER%" echo started
powershell.exe -NoProfile -NonInteractive -Command "Start-Sleep -Seconds 120"
exit /b 0
"@ | Set-Content -Path $fakeCodex -Encoding Ascii
    $env:DIVAN_FAKE_AGENT_MARKER = $agentMarker
    $env:PATH = "$fakeBin;$previousPath"

    $crashTask = Invoke-OttomanCore @{
        command = "task.create"
        task_id = "DIV-CRASH-RECOVERY"
        title = "Recover interrupted installed Core execution"
        project_id = $project.project_id
        engine_id = "native"
    }
    $crashPlanned = Invoke-OttomanCore @{ command = "task.plan"; task_id = $crashTask.task_id }
    if ($crashPlanned.state -ne "planned") {
        throw "Crash-recovery fixture did not enter planned state"
    }

    $startInput = Join-Path $root "crash-start.json"
    $startOutput = Join-Path $root "crash-start.stdout.txt"
    $startError = Join-Path $root "crash-start.stderr.txt"
    @{
        command = "task.start"
        task_id = $crashTask.task_id
        approve_execution = $true
        engine_id = "native"
        agent = "codex"
        prompt = "Deterministic lifecycle crash fixture; do not modify files."
    } | ConvertTo-Json -Compress -Depth 20 | Set-Content -Path $startInput -Encoding utf8

    $interruptedCore = Start-Process -FilePath $CoreExe `
        -RedirectStandardInput $startInput `
        -RedirectStandardOutput $startOutput `
        -RedirectStandardError $startError `
        -PassThru

    $agentStarted = $false
    foreach ($attempt in 1..30) {
        if (Test-Path $agentMarker) {
            $agentStarted = $true
            break
        }
        if ($interruptedCore.HasExited) {
            break
        }
        Start-Sleep -Seconds 1
    }
    if (-not $agentStarted) {
        $stdout = if (Test-Path $startOutput) { (Get-Content $startOutput -Raw) } else { "" }
        $stderr = if (Test-Path $startError) { (Get-Content $startError -Raw) } else { "" }
        throw "Fake worker was not invoked before crash injection. stdout=$stdout stderr=$stderr"
    }

    $duringExecution = Invoke-OttomanCore @{ command = "task.get"; task_id = $crashTask.task_id }
    $pendingDuringExecution = Get-OptionalProperty -Object $duringExecution.metadata -Name "execution_pending"
    if ($duringExecution.state -ne "running" -or $null -eq $pendingDuringExecution) {
        throw "Core did not persist execution_pending before invoking the worker"
    }
    if (-not $duringExecution.mandate_id) {
        throw "Mutating execution did not receive a Core-owned mandate before worker invocation"
    }
    $crashMandate = $duringExecution.mandate_id

    Stop-ProcessTree -Process $interruptedCore
    $interruptedCore = $null

    $afterCrash = Invoke-OttomanCore @{ command = "task.get"; task_id = $crashTask.task_id }
    $pendingAfterCrash = Get-OptionalProperty -Object $afterCrash.metadata -Name "execution_pending"
    if ($afterCrash.state -ne "running" -or $null -eq $pendingAfterCrash) {
        throw "Interrupted execution was not left in recoverable persisted RUNNING state"
    }
    if ($afterCrash.mandate_id -ne $crashMandate) {
        throw "Restart changed Core-owned execution authority"
    }

    $recovered = Invoke-OttomanCore @{ command = "task.recover.interrupted"; task_id = $crashTask.task_id }
    if ($recovered.state -ne "retry") {
        throw "Interrupted execution did not recover fail-closed to RETRY"
    }
    $pendingAfterRecovery = Get-OptionalProperty -Object $recovered.metadata -Name "execution_pending"
    if ($null -ne $pendingAfterRecovery) {
        throw "Recovered execution retained a stale execution_pending record"
    }
    if (-not $recovered.metadata.execution.interrupted -or $recovered.metadata.execution.ok) {
        throw "Recovered execution did not persist an explicit interrupted failure receipt"
    }
    if ($recovered.mandate_id -ne $crashMandate) {
        throw "Recovery reconstructed or replaced the persisted mandate"
    }

    $recoveryEvidenceRows = @(Invoke-OttomanCore @{ command = "evidence.list"; task_id = $crashTask.task_id })
    $recoveryEvidence = $recoveryEvidenceRows | Where-Object { $_.kind -eq "recovery" } | Select-Object -Last 1
    if (-not $recoveryEvidence -or $recoveryEvidence.status -ne "retry" -or $recoveryEvidence.data.resumed -ne $false) {
        throw "Recovery evidence does not prove that mutation remained stopped"
    }
    if ($recoveryEvidence.data.mandate_id -ne $crashMandate) {
        throw "Recovery evidence is not bound to the interrupted mandate"
    }

    $retryWithoutApproval = @{
        command = "task.start"
        task_id = $crashTask.task_id
        engine_id = "native"
        agent = "codex"
        prompt = "This retry must be rejected because approval is omitted."
    } | ConvertTo-Json -Compress -Depth 20
    $retryLines = @($retryWithoutApproval | & $CoreExe)
    $retryExitCode = $LASTEXITCODE
    $retryText = ($retryLines -join "`n").Trim()
    if (-not $retryText) {
        throw "Retry-without-approval returned no protocol response"
    }
    $retryResponse = $retryText | ConvertFrom-Json
    if ($retryExitCode -eq 0 -or $retryResponse.ok -or $retryResponse.error.code -ne "DESKTOP_EXECUTION_APPROVAL_REQUIRED") {
        throw "Recovered RETRY was able to start without a fresh explicit execution approval"
    }
    $afterRejectedRetry = Invoke-OttomanCore @{ command = "task.get"; task_id = $crashTask.task_id }
    if ($afterRejectedRetry.state -ne "retry" -or $afterRejectedRetry.mandate_id -ne $crashMandate) {
        throw "Rejected retry mutated persisted Core state or authority"
    }

    # Reset the fake worker before probing the Orca first-run matrix.
    $env:PATH = $previousPath
    $env:DIVAN_FAKE_AGENT_MARKER = $previousFakeAgentMarker

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

    $absent = Invoke-OttomanCore @{ command = "readiness" }
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

    $present = Invoke-OttomanCore @{ command = "readiness" }
    $presentOrca = Get-Tool -Readiness $present -Id "orca"
    $capabilities = Invoke-OttomanCore @{ command = "capabilities" }
    if (-not $presentOrca.available -or -not (@($present.engines) -contains "orca")) {
        throw "Orca-present first run did not discover the replaceable Orca engine"
    }
    if ($capabilities.product -ne "Ottoman") {
        throw "Execution engine discovery changed Core product authority"
    }
    if (-not (@($capabilities.features) -contains "mandate-gate") -or -not (@($capabilities.features) -contains "approval-gate")) {
        throw "Orca-present first run bypassed Ottoman mandate/approval authority capabilities"
    }

    $expectedCommit = (& git rev-parse HEAD).Trim()
    $expectedTree = (& git rev-parse 'HEAD^{tree}').Trim()
    $buildProvenance = $capabilities.build_provenance
    if (-not $buildProvenance -or $buildProvenance.source_commit -ne $expectedCommit -or $buildProvenance.source_tree -ne $expectedTree) {
        throw "Lifecycle evidence is not bound to the exact installed Core source identity"
    }

    $evidence = [ordered]@{
        schema_version = 2
        status = "pass"
        source_commit = $expectedCommit
        source_tree = $expectedTree
        desktop_process_restarts = 2
        persisted_task_state = $afterSecond.state
        persisted_task_has_mandate = ($null -ne $afterSecond.mandate_id)
        interrupted_execution_observed = $true
        interrupted_execution_state = $afterCrash.state
        recovered_state = $recovered.state
        recovery_resumed_mutation = [bool]$recoveryEvidence.data.resumed
        retry_without_approval_rejected = $true
        recovery_evidence_sha256 = $recoveryEvidence.sha256
        mandate_preserved_across_recovery = ($recovered.mandate_id -eq $crashMandate)
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
    if ($null -ne $interruptedCore) {
        Stop-ProcessTree -Process $interruptedCore
    }
    $env:DIVAN_DATA_DIR = $previousDataDir
    $env:PATH = $previousPath
    $env:APPDATA = $previousAppData
    $env:LOCALAPPDATA = $previousLocalAppData
    $env:USERPROFILE = $previousUserProfile
    $env:DIVAN_FAKE_AGENT_MARKER = $previousFakeAgentMarker
}
