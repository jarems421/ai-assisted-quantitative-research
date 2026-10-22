"""Fixed synthetic PowerShell event fixture. No WMI, accounts, Claude or network."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
CASES = ('collision', 'concurrent', 'disk_failure', 'missing_object')
if len(sys.argv) != 2 or sys.argv[1] not in CASES or os.name != 'nt':
    raise SystemExit('fixed Windows fixture case required')
case = sys.argv[1]

SCRIPT = r'''
$scoutFixtureWall = [Diagnostics.Stopwatch]::StartNew()
[Console]::Error.WriteLine('SCOUT_FIXTURE_ENTERED')
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
function Assert-Fixture($Condition, [string]$Reason) { if (-not $Condition) { throw $Reason } }
# Extract function definitions only. Never execute the watcher body, privilege
# checks, WMI subscriptions, account sampling or its private output paths.
foreach ($scoutSource in @('queue.ps1', 'watch.ps1')) {
    $scoutParseTokens = $null; $scoutParseErrors = $null
    $scoutAst = [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $env:SCOUT_FIXTURE_ROOT ('src/research/opportunity_scout/n1_preflight/' + $scoutSource)), [ref]$scoutParseTokens, [ref]$scoutParseErrors)
    Assert-Fixture ($scoutParseErrors.Count -eq 0) 'fixture source syntax'
    foreach ($scoutFunction in $scoutAst.FindAll({ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $false)) {
        . ([scriptblock]::Create($scoutFunction.Extent.Text))
    }
}
[Console]::Error.WriteLine('SCOUT_FIXTURE_FUNCTIONS_READY:' + $scoutFixtureWall.ElapsedMilliseconds)
$scoutFirst = 'FIXTURE-A-' + [guid]::NewGuid()
$scoutSecond = 'FIXTURE-B-' + [guid]::NewGuid()
$scoutOther = 'FIXTURE-OTHER-' + [guid]::NewGuid()
$scoutSources = @($scoutFirst, $scoutSecond, $scoutOther)
$scoutFile = [IO.File]::Open((Join-Path $env:SCOUT_FIXTURE_DIRECTORY 'events.jsonl'), [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
$scoutWriter = New-Object IO.StreamWriter($scoutFile, (New-Object Text.UTF8Encoding($false)))
$scoutSeq = 0; $scoutPrevious = '0' * 64
$scoutClock = [Diagnostics.Stopwatch]::StartNew()
$scoutSummary = [ordered]@{fixture = $true; case = $env:SCOUT_FIXTURE_CASE; claude_invocations = 0; wmi_subscriptions = 0}
$scoutTimerA = $null; $scoutTimerB = $null
[Console]::Error.WriteLine('SCOUT_FIXTURE_WRITER_READY:' + $scoutFixtureWall.ElapsedMilliseconds)
try {
    Write-ScoutRecord 'HEADER' ([ordered]@{schema = 'SCOUT_N1_PROCESS_OBSERVER_V002'; pid = 10; session = 'FICTIONAL_NOT_REGISTERED'; claude_invocations = 0})
    Write-ScoutRecord 'SNAPSHOT' ([ordered]@{processes = @()})
    Write-ScoutRecord 'HEARTBEAT' ([ordered]@{subscriptions_present = $true})
    [Console]::Error.WriteLine('SCOUT_FIXTURE_CASE_STARTED:' + $scoutFixtureWall.ElapsedMilliseconds)
    if ($env:SCOUT_FIXTURE_CASE -eq 'concurrent') {
        $scoutTimerA = New-Object Timers.Timer 1
        $scoutTimerB = New-Object Timers.Timer 1
        $null = Register-ObjectEvent -InputObject $scoutTimerA -EventName Elapsed -SourceIdentifier $scoutFirst
        $null = Register-ObjectEvent -InputObject $scoutTimerB -EventName Elapsed -SourceIdentifier $scoutSecond
        $scoutTimerA.Start(); $scoutTimerB.Start()
        $scoutProcessed = 0; $scoutDuplicateIds = 0
        $scoutSeenIds = New-Object 'System.Collections.Generic.HashSet[int]'
        $scoutSeenObjects = New-Object 'System.Collections.Generic.HashSet[System.Management.Automation.PSEventArgs]'
        $scoutRun = [Diagnostics.Stopwatch]::StartNew()
        while ($scoutRun.Elapsed.TotalSeconds -lt 2) {
            foreach ($scoutItem in @(Get-ScoutQueuedEvents -SourceIdentifiers @($scoutFirst, $scoutSecond))) {
                Assert-Fixture ($scoutSeenObjects.Add($scoutItem)) 'same object processed twice'
                if (-not $scoutSeenIds.Add($scoutItem.EventIdentifier)) { $scoutDuplicateIds++ }
                Write-ScoutRecord 'FICTIONAL_TIMER' ([ordered]@{queue_event_identifier = [int]$scoutItem.EventIdentifier})
                Acknowledge-ScoutQueuedEvent -QueuedEvent $scoutItem
                $scoutProcessed++
            }
        }
        $scoutTimerA.Stop(); $scoutTimerB.Stop()
        Start-Sleep -Milliseconds 100
        foreach ($scoutItem in @(Get-ScoutQueuedEvents -SourceIdentifiers @($scoutFirst, $scoutSecond))) {
            Assert-Fixture ($scoutSeenObjects.Add($scoutItem)) 'same queued object duplicated'
            Write-ScoutRecord 'FICTIONAL_TIMER' ([ordered]@{queue_event_identifier = [int]$scoutItem.EventIdentifier})
            Acknowledge-ScoutQueuedEvent -QueuedEvent $scoutItem
            $scoutProcessed++
        }
        Assert-Fixture ($scoutProcessed -ge 10) 'insufficient concurrent fixture events'
        $scoutSummary.processed = $scoutProcessed
        $scoutSummary.duplicate_numeric_ids_observed = $scoutDuplicateIds
    } else {
        Add-Type -TypeDefinition 'public class ScoutSyntheticEventArgs : System.EventArgs { public object NewEvent { get; set; } }'
        $scoutArgs = New-Object ScoutSyntheticEventArgs
        $scoutArgs.NewEvent = [pscustomobject]@{ProcessID = 50; ParentProcessID = 10; ProcessName = 'python.exe'; TIME_CREATED = [uint64]101}
        $scoutA = New-Event -SourceIdentifier $scoutFirst -EventArguments $scoutArgs
        $scoutArgsB = New-Object ScoutSyntheticEventArgs
        $scoutArgsB.NewEvent = [pscustomobject]@{ProcessID = 50; ProcessName = 'python.exe'; TIME_CREATED = [uint64]102}
        $scoutB = New-Event -SourceIdentifier $scoutSecond -EventArguments $scoutArgsB
        # A deterministic collision, not a fabricated process/provider event.
        $scoutEventIdProperty = [System.Management.Automation.PSEventArgs].GetProperty('EventIdentifier')
        $scoutEventIdProperty.SetValue($scoutA, 73, $null)
        $scoutEventIdProperty.SetValue($scoutB, 73, $null)
        if ($env:SCOUT_FIXTURE_CASE -eq 'collision') {
            $scoutUnrelated = New-Event -SourceIdentifier $scoutOther
            $scoutEventIdProperty.SetValue($scoutUnrelated, 73, $null)
            Write-ScoutQueuedProcessEvent -QueuedEvent $scoutA -StartSource $scoutFirst -StopSource $scoutSecond
            Assert-Fixture (@(Get-ScoutQueuedEvents -SourceIdentifiers @($scoutSecond)).Count -eq 1) 'collision dropped second event'
            Assert-Fixture (@(Get-ScoutQueuedEvents -SourceIdentifiers @($scoutOther)).Count -eq 1) 'unrelated event removed'
            Write-ScoutQueuedProcessEvent -QueuedEvent $scoutB -StartSource $scoutFirst -StopSource $scoutSecond
            Assert-Fixture (@(Get-ScoutQueuedEvents -SourceIdentifiers @($scoutFirst, $scoutSecond)).Count -eq 0) 'owned events not acknowledged'
            Assert-Fixture (@(Get-ScoutQueuedEvents -SourceIdentifiers @($scoutOther)).Count -eq 1) 'unrelated collision was removed'
            $scoutSummary.colliding_events_preserved = 2
            $scoutSummary.unrelated_event_retained = $true
        } elseif ($env:SCOUT_FIXTURE_CASE -eq 'disk_failure') {
            function Write-ScoutRecord { throw 'SYNTHETIC_DISK_FAILURE' }
            $scoutFailed = $false
            try { Write-ScoutQueuedProcessEvent -QueuedEvent $scoutA -StartSource $scoutFirst -StopSource $scoutSecond } catch { $scoutFailed = $true }
            Assert-Fixture $scoutFailed 'write failure ignored'
            $scoutPending = @(Get-ScoutQueuedEvents -SourceIdentifiers @($scoutFirst))
            Assert-Fixture ($scoutPending.Count -eq 1 -and [object]::ReferenceEquals($scoutPending[0], $scoutA)) 'event acknowledged before failed persistence'
            $scoutSummary.failed_write_event_still_queued = $true
        } else {
            Acknowledge-ScoutQueuedEvent -QueuedEvent $scoutA
            $scoutFailed = $false
            try { Write-ScoutQueuedProcessEvent -QueuedEvent $scoutA -StartSource $scoutFirst -StopSource $scoutSecond } catch { $scoutFailed = $true }
            Assert-Fixture $scoutFailed 'missing exact object ignored'
            Assert-Fixture (@(Get-ScoutQueuedEvents -SourceIdentifiers @($scoutSecond)).Count -eq 1) 'missing object consumed collision peer'
            $scoutSummary.missing_object_failed_closed = $true
        }
    }
    if ($env:SCOUT_FIXTURE_CASE -in @('collision', 'concurrent')) {
        Write-ScoutRecord 'END' ([ordered]@{reason = 'STOP_REQUEST'; coverage_certified = $false})
    }
    [Console]::Error.WriteLine('SCOUT_FIXTURE_CASE_DONE:' + $scoutFixtureWall.ElapsedMilliseconds)
} finally {
    if ($null -ne $scoutTimerA) { $scoutTimerA.Stop(); $scoutTimerA.Dispose() }
    if ($null -ne $scoutTimerB) { $scoutTimerB.Stop(); $scoutTimerB.Dispose() }
    foreach ($scoutSourceId in $scoutSources) { Unregister-Event -SourceIdentifier $scoutSourceId -ErrorAction SilentlyContinue }
    foreach ($scoutPending in @(Get-ScoutQueuedEvents -SourceIdentifiers $scoutSources)) { Acknowledge-ScoutQueuedEvent -QueuedEvent $scoutPending }
    $scoutWriter.Dispose(); $scoutFile.Dispose()
}
[Console]::Error.WriteLine('SCOUT_FIXTURE_CLEANED:' + $scoutFixtureWall.ElapsedMilliseconds)
$scoutSummary.fixture_elapsed_ms = $scoutFixtureWall.ElapsedMilliseconds
$scoutSummary | ConvertTo-Json -Compress
'''

with tempfile.TemporaryDirectory(prefix='scout-queue-fictional-') as directory:
    # Windows PowerShell startup needs the ordinary OS locations too. Never
    # inherit account/provider variables, user profiles/scripts or PSModulePath.
    sys.path.insert(0, str(ROOT))
    from src.research.opportunity_scout.v004_runtime import OS_ENV
    env = {k: v for k, v in os.environ.items() if k.upper() in OS_ENV}
    env['PSModulePath'] = str(Path(os.environ['SystemRoot']) / 'System32/WindowsPowerShell/v1.0/Modules')
    env.update(SCOUT_FIXTURE_ROOT=str(ROOT), SCOUT_FIXTURE_DIRECTORY=directory, SCOUT_FIXTURE_CASE=case)
    shell = Path(os.environ['SystemRoot']) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
    try:
        result = subprocess.run([str(shell), '-NoLogo', '-NoProfile', '-NonInteractive', '-Command', SCRIPT],
                                stdin=subprocess.DEVNULL, capture_output=True, timeout=60, env=env, shell=False)
    except subprocess.TimeoutExpired as error:
        stages = [line for line in (error.stderr or b'').decode(errors='replace').splitlines() if line.startswith('SCOUT_FIXTURE_')]
        print(json.dumps({'fixture': True, 'case': case, 'failure': 'POWERSHELL_FIXTURE_TIMEOUT', 'stages': stages}))
        raise SystemExit(1)
    if result.returncode:
        print(result.stderr.decode('utf-8', errors='replace'))
        raise SystemExit(result.returncode)
    report = json.loads(result.stdout)
    raw = (Path(directory) / 'events.jsonl').read_bytes()
    previous = '0' * 64
    records = []
    for index, line in enumerate(raw.splitlines(), 1):
        frame = json.loads(line)
        digest = hashlib.sha256(frame['record'].encode('utf-8')).hexdigest()
        record = json.loads(frame['record'])
        assert digest == frame['sha256'] and record['previous'] == previous and record['seq'] == index
        previous = digest
        records.append(record)
    from src.research.opportunity_scout.n1_preflight.monitor import audit, Refused
    if case == 'collision':
        audit(Path(directory) / 'events.jsonl')
        assert [r['data']['queue_event_identifier'] for r in records if r['kind'] in ('START', 'EXIT')] == [73, 73]
        assert len([r for r in records if r['kind'] == 'QUEUE_ACK']) == 2
    elif case in ('disk_failure', 'missing_object'):
        try:
            audit(Path(directory) / 'events.jsonl')
        except Refused:
            pass
        else:
            raise AssertionError('incomplete fixture falsely accepted')
        assert not any(r['kind'] == 'QUEUE_ACK' for r in records)
    report.update(frame_chain_verified=True, records=len(records), raw_sha256=hashlib.sha256(raw).hexdigest())
    print(json.dumps(report))
