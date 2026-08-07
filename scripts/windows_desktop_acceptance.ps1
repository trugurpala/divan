param(
    [string]$CorePath = "",
    [string]$Version = "",
    [string]$Output = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$sourceCommit = (& git -C $RepoRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $sourceCommit -notmatch '^[0-9a-f]{40}$') {
    throw "Divan source commit could not be resolved"
}
$sourceTree = (& git -C $RepoRoot rev-parse 'HEAD^{tree}').Trim()
if ($LASTEXITCODE -ne 0 -or $sourceTree -notmatch '^[0-9a-f]{40}$') {
    throw "Divan source tree could not be resolved"
}
if (-not $Version) {
    $Version = (Get-Content (Join-Path $RepoRoot "VERSION") -Raw).Trim()
}
if (-not $Output) {
    $Output = Join-Path $RepoRoot ".divan/evidence/windows-desktop-acceptance-v$Version.json"
}
if (-not $CorePath) {
    $installRoot = Join-Path $env:LOCALAPPDATA "Divan"
    $core = Get-ChildItem $installRoot -Filter "divan-core*.exe" -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $core) {
        throw "Installed Divan Core sidecar was not found. Install the current NSIS bundle first."
    }
    $CorePath = $core.FullName
}
if (-not (Test-Path $CorePath)) {
    throw "Divan Core sidecar not found: $CorePath"
}

$acceptanceRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("divan-acceptance-" + [guid]::NewGuid().ToString("N"))
$projectRoot = Join-Path $acceptanceRoot "project"
$dataRoot = Join-Path $acceptanceRoot "state"
New-Item -ItemType Directory -Path $projectRoot -Force | Out-Null
New-Item -ItemType Directory -Path $dataRoot -Force | Out-Null
$env:DIVAN_DATA_DIR = $dataRoot

function Invoke-Core([hashtable]$Request) {
    $json = $Request | ConvertTo-Json -Depth 20 -Compress
    $lines = $json | & $CorePath
    if ($LASTEXITCODE -ne 0) {
        throw "Divan Core exited with code $LASTEXITCODE for command $($Request.command)"
    }
    $raw = ($lines -join "`n").Trim()
    if (-not $raw) {
        throw "Divan Core returned no output for command $($Request.command)"
    }
    $envelope = $raw | ConvertFrom-Json
    if (-not $envelope.ok) {
        throw "Divan Core command $($Request.command) failed: $($envelope.error.code) $($envelope.error.message)"
    }
    return $envelope.result
}

function Invoke-Git([string[]]$Arguments) {
    & git -C $projectRoot @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "git $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
    }
}

try {
    $capabilities = Invoke-Core @{ command = "capabilities" }
    $build = $capabilities.build_provenance
    if (-not $build -or $build.source_commit -notmatch '^[0-9a-f]{40}$' -or $build.source_tree -notmatch '^[0-9a-f]{40}$') {
        throw "Installed Divan Core does not expose release build provenance"
    }
    if ($build.source_tree -ne $sourceTree) {
        throw "Installed Divan Core source tree does not match the acceptance checkout"
    }

    git init $projectRoot | Out-Null
    Invoke-Git @("config", "user.name", "Divan Acceptance")
    Invoke-Git @("config", "user.email", "acceptance@invalid.local")
    Set-Content -Path (Join-Path $projectRoot "README.md") -Value "# Divan acceptance fixture" -Encoding utf8
    Invoke-Git @("add", "README.md")
    Invoke-Git @("commit", "-m", "test: seed Divan acceptance fixture")

    $readiness = Invoke-Core @{ command = "readiness" }
    $tools = @{}
    foreach ($tool in $readiness.tools) {
        $tools[$tool.id] = $tool
    }
    if (-not $tools.ContainsKey("git") -or -not $tools["git"].available) {
        throw "Git is required for Windows acceptance"
    }

    $releaseAgents = @(@("codex", "claude") | Where-Object { $tools.ContainsKey($_) -and $tools[$_].available })
    if ($releaseAgents.Count -lt 2) {
        throw "Stable release acceptance requires both installed Codex and Claude Code so worker and reviewer are different agents"
    }
    $worker = "codex"
    if (-not $tools[$worker].available) {
        $worker = "claude"
    }

    $project = Invoke-Core @{ command = "project.register"; root = $projectRoot }
    $task = Invoke-Core @{
        command = "task.create"
        title = "Create divan-acceptance.txt containing exactly DIVAN_ACCEPTANCE_OK and do not modify any other tracked file."
        project_id = $project.project_id
        engine_id = "native"
    }
    $task = Invoke-Core @{ command = "task.plan"; task_id = $task.task_id; reason = "real-user Windows release acceptance" }
    $task = Invoke-Core @{
        command = "task.start"
        task_id = $task.task_id
        approve_execution = $true
        engine_id = "native"
        agent = $worker
        prompt = "Create a new file named divan-acceptance.txt containing exactly DIVAN_ACCEPTANCE_OK followed by a newline. Do not modify any other tracked file. Finish after creating that file."
    }
    if ($task.state -ne "running") {
        throw "Authenticated worker did not reach running state: $($task.state)"
    }

    $diff = Invoke-Core @{ command = "task.diff"; task_id = $task.task_id }
    if (-not $diff.diff.Contains("DIVAN_ACCEPTANCE_OK")) {
        throw "Worker completed without the expected acceptance diff"
    }

    $review = Invoke-Core @{ command = "task.review.auto"; task_id = $task.task_id }
    if ($review.review.verdict -ne "PASS") {
        throw "Independent review did not pass: $($review.review.verdict)"
    }
    $reviewer = $review.task.metadata.automated_review.reviewer
    if ($reviewer -notin @("claude", "codex")) {
        throw "Independent reviewer was not Claude or Codex: $reviewer"
    }
    if ($reviewer -eq $worker) {
        throw "Release acceptance requires worker and reviewer to be different agents"
    }
    if (-not $review.task.metadata.review_snapshot.diff_sha256) {
        throw "Review was not bound to a staged diff SHA-256"
    }

    $task = Invoke-Core @{ command = "task.approval.request"; task_id = $task.task_id }
    $task = Invoke-Core @{ command = "task.approve"; task_id = $task.task_id; approved = $true }
    if ($task.state -ne "merged") {
        throw "Guarded merge did not reach merged state: $($task.state)"
    }
    if (-not $task.metadata.merge.diff_sha256 -or -not $task.metadata.merge.commit_sha) {
        throw "Guarded merge metadata is incomplete"
    }
    if ($task.metadata.merge.diff_sha256 -ne $review.task.metadata.review_snapshot.diff_sha256) {
        throw "Merged diff hash does not match the independently reviewed snapshot"
    }

    $acceptanceFile = Join-Path $projectRoot "divan-acceptance.txt"
    if (-not (Test-Path $acceptanceFile)) {
        throw "Fast-forward merge did not place the acceptance file on the project branch"
    }
    $content = (Get-Content $acceptanceFile -Raw).Trim()
    if ($content -ne "DIVAN_ACCEPTANCE_OK") {
        throw "Acceptance file content is incorrect"
    }
    $status = (& git -C $projectRoot status --porcelain) -join "`n"
    if ($LASTEXITCODE -ne 0 -or $status.Trim()) {
        throw "Project is not clean after guarded merge: $status"
    }

    $evidence = @(Invoke-Core @{ command = "evidence.list"; task_id = $task.task_id })
    $kinds = @($evidence | ForEach-Object { $_.kind } | Sort-Object -Unique)
    foreach ($kind in @("execution", "review", "approval")) {
        if ($kind -notin $kinds) {
            throw "Acceptance evidence is missing required kind: $kind"
        }
    }
    foreach ($record in $evidence) {
        if (-not $record.sha256) {
            throw "Acceptance evidence contains a record without SHA-256"
        }
    }

    $result = [ordered]@{
        schema_version = 3
        product = "Divan"
        version = $Version
        platform = "windows"
        source_commit = $sourceCommit
        source_tree = $sourceTree
        core_source_commit = $build.source_commit
        core_source_tree = $build.source_tree
        result = "PASS"
        authenticated_worker = $true
        worker_agent = $worker
        authenticated_reviewer = $true
        independent_reviewer = $true
        reviewer = $reviewer
        review_bound_to_diff = $true
        ff_only_merge = $true
        task_state = $task.state
        evidence_kinds = $kinds
        review_diff_sha256 = $review.task.metadata.review_snapshot.diff_sha256
        merged_commit_sha = $task.metadata.merge.commit_sha
    }
    $outputDir = Split-Path -Parent $Output
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    $result | ConvertTo-Json -Depth 10 | Set-Content -Path $Output -Encoding utf8
    Write-Host "PASS: source-bound cross-agent Windows acceptance evidence written to $Output"
}
finally {
    Remove-Item Env:DIVAN_DATA_DIR -ErrorAction SilentlyContinue
    if (Test-Path $acceptanceRoot) {
        Remove-Item $acceptanceRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
