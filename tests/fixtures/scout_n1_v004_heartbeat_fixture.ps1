# Fictional events and virtual time only. Never execute watcher startup, WMI,
# account sampling, a sentinel or a private output path.
param([string]$FixtureRoot, [string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
Add-Type @'
using System;
using System.IO;
public class ScoutHeartbeatClock {
    public long Now;
    public long ElapsedMilliseconds { get { return Now; } }
}
public class ScoutHeartbeatFile : IDisposable {
    public FileStream Inner;
    public ScoutHeartbeatClock Clock;
    public long Latency;
    public long SecondLatency;
    public int SlowCall;
    public int Calls;
    public bool FailNext;
    public long Length { get { return Inner.Length; } }
    public void Flush(bool durable) {
        Calls++;
        if (FailNext) { FailNext = false; throw new IOException("FICTIONAL_PERSISTENCE_FAILURE"); }
        Inner.Flush(durable);
        Clock.Now += (Calls == SlowCall) ? 6000 : ((Calls == 2 && SecondLatency > 0) ? SecondLatency : Latency);
    }
    public void Dispose() { Inner.Dispose(); }
}
public class ScoutHeartbeatArgs : EventArgs { public object NewEvent { get; set; } }
'@
function Import-FixtureFunctions([string]$Version) {
    foreach ($scoutName in @('n1_preflight/queue.ps1', ($Version + '/watch.ps1'))) {
        $tokens = $null; $errors = $null
        $ast = [System.Management.Automation.Language.Parser]::ParseFile(
            (Join-Path $FixtureRoot ('src/research/opportunity_scout/' + $scoutName)), [ref]$tokens, [ref]$errors)
        if ($errors.Count) { throw 'FIXTURE_SOURCE_SYNTAX' }
        foreach ($fn in $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $false)) {
            # Global scope is confined to this fresh fixture-only PowerShell.
            . ([scriptblock]::Create($fn.Extent.Text.Replace(('function ' + $fn.Name), ('function global:' + $fn.Name))))
        }
        if ($Version -eq 'n1_preflight' -and $scoutName.EndsWith('/watch.ps1')) {
            $loop = @($ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.WhileStatementAst] -and $n.Condition.Extent.Text.Contains('Elapsed.TotalSeconds') }, $false))[0]
            $body = $loop.Body.Extent.Text
            $script:legacyStep = [scriptblock]::Create($body.Substring(1, $body.Length - 2))
        }
    }
}
$reports = @()
foreach ($case in @('legacy_burst','burst','empty','slow_event','slow_ack','late_heartbeat',
                    'first_slow_heartbeat','late_queue','late_subscription','missing_subscription',
                    'overflow','malformed','claude','persistence_failure','shutdown','shutdown_slow','shutdown_end_slow')) {
    $version = $(if ($case -eq 'legacy_burst') { 'n1_preflight' } else { 'n1_preflight_v004' })
    Import-FixtureFunctions $version
    $script:scoutClock = New-Object ScoutHeartbeatClock
    $script:scoutFile = New-Object ScoutHeartbeatFile
    $script:scoutFile.Clock = $script:scoutClock
    $path = Join-Path $OutputDirectory ($case + '.jsonl')
    $script:scoutFile.Inner = [IO.File]::Open($path, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
    $script:scoutWriter = New-Object IO.StreamWriter($script:scoutFile.Inner, (New-Object Text.UTF8Encoding($false)))
    $script:scoutSeq = 0; $script:scoutPrevious = '0' * 64
    $script:scoutLastRecordAt = $null; $script:scoutLastHeartbeat = $null
    $script:scoutWritePoisoned = $false
    $script:scoutDirectory = $OutputDirectory
    $script:scoutSubscriptions = @('FICTIONAL_START', 'FICTIONAL_EXIT')
    $script:scoutStartId = $script:scoutSubscriptions[0]
    $script:scoutStopId = $script:scoutSubscriptions[1]
    $script:missingSubscription = $false; $script:slowSubscription = $false
    function global:Get-EventSubscriber {
        param($SourceIdentifier, $ErrorAction)
        if ($script:slowSubscription) { $script:scoutClock.Now += 6000 }
        if (-not $script:missingSubscription) { [pscustomobject]@{SourceIdentifier=$SourceIdentifier} }
    }
    # No actual subscriptions exist. Shutdown tests replace only unsubscribe.
    function global:Unregister-Event { param($SourceIdentifier, $ErrorAction) }
    $errorCode = $null
    try {
        $schema = $(if ($version -eq 'n1_preflight') { 'SCOUT_N1_PROCESS_OBSERVER_V003' } else { 'SCOUT_N1_PROCESS_OBSERVER_V004' })
        Write-ScoutRecord 'HEADER' ([ordered]@{schema=$schema;pid=10;session='FICTIONAL';claude_invocations=0})
        Write-ScoutRecord 'SNAPSHOT' ([ordered]@{processes=@()})
        if ($case -eq 'legacy_burst') {
            Write-ScoutRecord 'HEARTBEAT' ([ordered]@{subscriptions_present=$true})
            $script:scoutLastHeartbeat = $script:scoutClock.Now
        } elseif ($case -ne 'first_slow_heartbeat') {
            Update-ScoutHeartbeat -Sources $script:scoutSubscriptions
        }
        $script:scoutFile.Calls = 0; $script:scoutFile.Latency = 150
        $count = $(if ($case -eq 'overflow') {10001} elseif ($case -in @('empty','late_heartbeat','first_slow_heartbeat','late_subscription')) {0} else {34})
        $objects = New-Object 'System.Collections.Generic.HashSet[System.Management.Automation.PSEventArgs]'
        for ($i = 0; $i -lt $count; $i++) {
            $argsObject = New-Object ScoutHeartbeatArgs
            $argsObject.NewEvent = [pscustomobject]@{ProcessID=(100+$i);ParentProcessID=10;ProcessName='fictional.exe';TIME_CREATED=[uint64](1000+$i)}
            if ($case -eq 'claude' -and $i -eq 16) { $argsObject.NewEvent.ProcessName='claude.exe' }
            if ($case -eq 'malformed') { $argsObject.NewEvent=[pscustomobject]@{ProcessName='fictional.exe'} }
            $obj = New-Event -SourceIdentifier $script:scoutSubscriptions[0] -EventArguments $argsObject
            # Numeric collisions must not change exact-object ACK or order.
            [System.Management.Automation.PSEventArgs].GetProperty('EventIdentifier').SetValue($obj, 73, $null)
            $null = $objects.Add($obj)
        }
        $unrelated = New-Event -SourceIdentifier 'FICTIONAL_UNRELATED'
        switch ($case) {
            'empty' { $script:scoutClock.Now=1000 }
            'slow_event' { $script:scoutFile.Latency=6000 }
            'slow_ack' { $script:scoutFile.SecondLatency=6000 }
            'late_heartbeat' { $script:scoutClock.Now=4000; $script:scoutFile.Latency=1500 }
            'first_slow_heartbeat' { $script:scoutFile.Latency=6000 }
            'late_subscription' { $script:scoutClock.Now=1000; $script:slowSubscription=$true }
            'missing_subscription' { $script:scoutClock.Now=1000; $script:missingSubscription=$true }
            'persistence_failure' { $script:scoutFile.FailNext=$true }
            'shutdown_slow' { $script:scoutFile.Latency=6000 }
            'shutdown_end_slow' { $script:scoutFile.Latency=3; $script:scoutFile.SlowCall=69 }
            'late_queue' {
                $script:queueRead = (Get-Command Get-ScoutQueuedEvents).ScriptBlock
                function global:Get-ScoutQueuedEvents {
                    param([string[]]$SourceIdentifiers)
                    $script:scoutClock.Now += 6000
                    & $script:queueRead -SourceIdentifiers $SourceIdentifiers
                }
            }
        }
        if ($case -eq 'legacy_burst') { . $script:legacyStep }
        elseif ($case.StartsWith('shutdown')) {
            # Cheap fixture writes can drain inside the shutdown deadline.
            if ($case -eq 'shutdown') { $script:scoutFile.Latency=3 }
            Complete-ScoutObservation -StartSource $script:scoutSubscriptions[0] -StopSource $script:scoutSubscriptions[1] -Reason 'STOP_REQUEST'
        } else { Invoke-ScoutObservationStep -Sources $script:scoutSubscriptions }
        if (-not $case.StartsWith('shutdown')) {
            Write-ScoutRecord 'END' ([ordered]@{reason='STOP_REQUEST';coverage_certified=$false})
        }
    } catch {
        $errorCode = $_.Exception.Message
        # Retain failure, never fabricate END. No deadline checks suppress ERROR.
        if (-not $script:scoutWritePoisoned) {
            Write-ScoutRecord 'ERROR' ([ordered]@{type='FICTIONAL_FAILURE';code=$errorCode})
        }
    } finally {
        $script:scoutWriter.Dispose(); $script:scoutFile.Dispose()
    }
    $queue = $ExecutionContext.Events.ReceivedEvents
    $pending = @($queue | Where-Object { $_.SourceIdentifier -in $script:scoutSubscriptions })
    $exactPending = $true
    foreach ($item in $pending) {
        if (-not $objects.Contains($item)) { $exactPending=$false }
    }
    $reports += [pscustomobject]@{case=$case;error=$errorCode;pending=$pending.Count;exact_pending=$exactPending;
        unrelated_retained=(@($queue | Where-Object {[object]::ReferenceEquals($_,$unrelated)}).Count -eq 1);
        last_heartbeat=$script:scoutLastHeartbeat;elapsed_ms=$script:scoutClock.Now}
    # Only fictional objects in this fresh fixture process are cleared.
    Get-Event -ErrorAction SilentlyContinue | ForEach-Object {
        Remove-Event -EventIdentifier $_.EventIdentifier -ErrorAction SilentlyContinue
    }
}
ConvertTo-Json -InputObject $reports -Depth 5 -Compress
