# One bounded process-event observation. Run as the same owner's administrator.
# Never launches Claude, reads account contents, or changes policy/settings.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot '../n1_preflight/queue.ps1')
$scoutRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../..'))
$scoutDirectory = Join-Path $scoutRoot '.research/opportunity_scout/n1-admin-observer-v004'
$scoutFile = $null
$scoutWriter = $null
$scoutSeq = 0
$scoutPrevious = '0' * 64
$scoutClock = [Diagnostics.Stopwatch]::StartNew()
$scoutStartId = 'ScoutStart-' + [guid]::NewGuid()
$scoutStopId = 'ScoutStop-' + [guid]::NewGuid()
$scoutSubscriptions = @()
$scoutLastHeartbeat = $null
$scoutLastRecordAt = $null
$scoutWritePoisoned = $false

function Write-ScoutRecord([string]$Kind, $Data) {
    # A failed write/flush may leave original partial or unconfirmed bytes.
    # Never append a purported chained recovery record after that failure.
    $script:scoutWritePoisoned = $true
    $script:scoutSeq++
    $script:scoutLastRecordAt = [long]$script:scoutClock.ElapsedMilliseconds
    $scoutRecord = [ordered]@{
        seq = $script:scoutSeq; previous = $script:scoutPrevious
        elapsed_ms = $script:scoutLastRecordAt
        kind = $Kind; data = $Data
    } | ConvertTo-Json -Depth 8 -Compress
    $scoutHasher = [Security.Cryptography.SHA256]::Create()
    try {
        $scoutDigest = ([BitConverter]::ToString($scoutHasher.ComputeHash([Text.Encoding]::UTF8.GetBytes($scoutRecord)))).Replace('-', '').ToLowerInvariant()
    } finally { $scoutHasher.Dispose() }
    if ($script:scoutFile.Length -gt 2097152) { throw 'OBSERVER_RECORDING_LIMIT' }
    $script:scoutWriter.WriteLine(([ordered]@{record = $scoutRecord; sha256 = $scoutDigest} | ConvertTo-Json -Compress))
    $script:scoutWriter.Flush()
    $script:scoutFile.Flush($true)
    $script:scoutPrevious = $scoutDigest
    $script:scoutWritePoisoned = $false
}

function Write-ScoutQueuedProcessEvent(
    [System.Management.Automation.PSEventArgs]$QueuedEvent,
    [string]$StartSource, [string]$StopSource
) {
    if ($QueuedEvent.SourceIdentifier -notin @($StartSource, $StopSource)) { throw 'UNEXPECTED_EVENT_SOURCE' }
    Assert-ScoutHeartbeatDeadline
    $scoutNative = $QueuedEvent.SourceEventArgs.NewEvent
    $scoutData = [ordered]@{pid = [int]$scoutNative.ProcessID; name = [string]$scoutNative.ProcessName
        event_filetime = [string]$scoutNative.TIME_CREATED
        queue_event_identifier = [int]$QueuedEvent.EventIdentifier}
    if ($QueuedEvent.SourceIdentifier -eq $StartSource) {
        $scoutData.parent_pid = [int]$scoutNative.ParentProcessID
        Write-ScoutRecord 'START' $scoutData
    } else { Write-ScoutRecord 'EXIT' $scoutData }
    Assert-ScoutHeartbeatDeadline
    $scoutPersistedSeq = $script:scoutSeq
    Acknowledge-ScoutQueuedEvent -QueuedEvent $QueuedEvent
    Assert-ScoutHeartbeatDeadline
    Write-ScoutRecord 'QUEUE_ACK' ([ordered]@{record_seq = $scoutPersistedSeq; queue_event_identifier = [int]$QueuedEvent.EventIdentifier})
    Assert-ScoutHeartbeatDeadline
}

function Assert-ScoutHeartbeatDeadline {
    if ($null -ne $script:scoutLastHeartbeat -and
        $script:scoutClock.ElapsedMilliseconds - $script:scoutLastHeartbeat -gt 5000) {
        throw 'HEARTBEAT_DEADLINE_EXPIRED'
    }
}

function Update-ScoutHeartbeat([string[]]$Sources) {
    Assert-ScoutHeartbeatDeadline
    if ($null -eq $script:scoutLastHeartbeat -or
        $script:scoutClock.ElapsedMilliseconds - $script:scoutLastHeartbeat -ge 1000) {
        foreach ($scoutSource in $Sources) {
            if (-not (Get-EventSubscriber -SourceIdentifier $scoutSource -ErrorAction SilentlyContinue)) {
                throw 'SUBSCRIPTION_LOST'
            }
            Assert-ScoutHeartbeatDeadline
        }
        Write-ScoutRecord 'HEARTBEAT' ([ordered]@{subscriptions_present = $true})
        # Check the OLD deadline before replacing it. Late persistence cannot
        # repair an expired window; anchor to record time, never flush return.
        Assert-ScoutHeartbeatDeadline
        if ($script:scoutClock.ElapsedMilliseconds - $script:scoutLastRecordAt -gt 5000) {
            throw 'HEARTBEAT_WRITE_DEADLINE_EXPIRED'
        }
        $script:scoutLastHeartbeat = $script:scoutLastRecordAt
    }
}

function Invoke-ScoutObservationStep([string[]]$Sources) {
    Assert-ScoutHeartbeatDeadline
    $scoutEvents = @(Get-ScoutQueuedEvents -SourceIdentifiers $Sources)
    Assert-ScoutHeartbeatDeadline
    foreach ($scoutEvent in $scoutEvents) {
        Write-ScoutQueuedProcessEvent -QueuedEvent $scoutEvent -StartSource $Sources[0] -StopSource $Sources[1]
        # Heartbeats never split a process record and its adjacent exact ACK.
        Update-ScoutHeartbeat -Sources $Sources
    }
    Update-ScoutHeartbeat -Sources $Sources
}

function Complete-ScoutObservation([string]$StartSource, [string]$StopSource, [string]$Reason) {
    Assert-ScoutHeartbeatDeadline
    # Stop delivery before draining. A failed unsubscribe/drain cannot emit END.
    foreach ($scoutSource in @($StartSource, $StopSource)) {
        Unregister-Event -SourceIdentifier $scoutSource -ErrorAction Stop
        Assert-ScoutHeartbeatDeadline
    }
    foreach ($scoutPending in @(Get-ScoutQueuedEvents -SourceIdentifiers @($StartSource, $StopSource))) {
        Write-ScoutQueuedProcessEvent -QueuedEvent $scoutPending -StartSource $StartSource -StopSource $StopSource
    }
    # Refuse visible late arrivals; this does not certify WMI losslessness.
    if (@(Get-ScoutQueuedEvents -SourceIdentifiers @($StartSource, $StopSource)).Count -ne 0) {
        throw 'OBSERVER_PENDING_EVENTS_AT_END'
    }
    Assert-ScoutHeartbeatDeadline
    Write-ScoutRecord 'END' ([ordered]@{reason = $Reason; coverage_certified = $false})
    Assert-ScoutHeartbeatDeadline
}

try {
    $scoutIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $scoutPrincipal = New-Object Security.Principal.WindowsPrincipal($scoutIdentity)
    if (-not $scoutPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'ADMINISTRATOR_OBSERVER_REQUIRED'
    }
    # Refuse links in every existing path component. Never remove an old run.
    $scoutParent = $scoutDirectory
    while ($scoutParent) {
        if (Test-Path -LiteralPath $scoutParent) {
            $scoutEntry = Get-Item -LiteralPath $scoutParent -Force
            if ($scoutEntry.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'LINK_PATH_REFUSED' }
        }
        $scoutParent = [IO.Path]::GetDirectoryName($scoutParent)
    }
    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($scoutDirectory)) | Out-Null
    # Exclusive directory creation is not portable in .NET; the exclusive claim
    # is the arbiter. Every subsequent file is CreateNew, never overwritten.
    [IO.Directory]::CreateDirectory($scoutDirectory) | Out-Null
    $scoutClaim = [IO.File]::Open((Join-Path $scoutDirectory 'observer.claim'), [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
    try {
        $scoutClaimBytes = [Text.Encoding]::UTF8.GetBytes('METADATA_ONLY_NO_CLAUDE_NO_RETRY')
        $scoutClaim.Write($scoutClaimBytes, 0, $scoutClaimBytes.Length)
        $scoutClaim.Flush($true)
    } finally { $scoutClaim.Dispose() }
    $scoutFile = [IO.File]::Open((Join-Path $scoutDirectory 'events.jsonl'), [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
    $scoutWriter = New-Object IO.StreamWriter($scoutFile, (New-Object Text.UTF8Encoding($false)))
    Write-ScoutRecord 'HEADER' ([ordered]@{schema = 'SCOUT_N1_PROCESS_OBSERVER_V004'; pid = $PID; session = [guid]::NewGuid().ToString(); claude_invocations = 0})
    # Subscribe before snapshot so short-lived starts aren't reduced to polling.
    $null = Register-WmiEvent -Namespace 'root\cimv2' -Class Win32_ProcessStartTrace -SourceIdentifier $scoutStartId
    $scoutSubscriptions += $scoutStartId
    $null = Register-WmiEvent -Namespace 'root\cimv2' -Class Win32_ProcessStopTrace -SourceIdentifier $scoutStopId
    $scoutSubscriptions += $scoutStopId
    $scoutSnapshot = @(Get-CimInstance Win32_Process -Property Name,ProcessId,ParentProcessId,CreationDate | ForEach-Object {
        [ordered]@{pid = [int]$_.ProcessId; parent_pid = [int]$_.ParentProcessId; name = [string]$_.Name
            creation_filetime = $(if ($null -eq $_.CreationDate) { $null } else { [string]$_.CreationDate.ToFileTimeUtc() })}
    })
    Write-ScoutRecord 'SNAPSHOT' ([ordered]@{processes = $scoutSnapshot})
    Write-Output 'OBSERVER_STARTED_METADATA_ONLY. Leave this administrator window open; do not run Claude here.'
    Update-ScoutHeartbeat -Sources $scoutSubscriptions
    while ($scoutClock.Elapsed.TotalSeconds -lt 360) {
        if (Test-Path -LiteralPath (Join-Path $scoutDirectory 'stop.request')) { break }
        Invoke-ScoutObservationStep -Sources $scoutSubscriptions
        Start-Sleep -Milliseconds 100
    }
    Complete-ScoutObservation -StartSource $scoutStartId -StopSource $scoutStopId -Reason $(if (Test-Path -LiteralPath (Join-Path $scoutDirectory 'stop.request')) { 'STOP_REQUEST' } else { 'TIME_LIMIT' })
    Write-Output 'OBSERVER_ENDED. This is not an authentication or N1 approval result.'
} catch {
    if ($null -ne $scoutWriter -and -not $scoutWritePoisoned) {
        try { Write-ScoutRecord 'ERROR' ([ordered]@{type = $_.Exception.GetType().Name; code = [string]$_.FullyQualifiedErrorId}) } catch {}
    }
    Write-Output 'OBSERVER_STOPPED. Preserve the directory; do not retry or remove its claim.'
    exit 1
} finally {
    foreach ($scoutSubscription in $scoutSubscriptions) { Unregister-Event -SourceIdentifier $scoutSubscription -ErrorAction SilentlyContinue }
    # Never remove unpersisted queue objects in failure cleanup.
    if ($null -ne $scoutWriter) { $scoutWriter.Dispose() }
    if ($null -ne $scoutFile) { $scoutFile.Dispose() }
}
