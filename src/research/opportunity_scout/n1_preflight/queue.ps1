# Local PowerShell queue operations, not provider/model event identifiers.
# Numeric EventIdentifier values can collide under concurrent producers.
function Get-ScoutQueuedEvents([string[]]$SourceIdentifiers) {
    $scoutQueue = $ExecutionContext.Events.ReceivedEvents
    $scoutPending = New-Object 'System.Collections.Generic.List[System.Management.Automation.PSEventArgs]'
    [Threading.Monitor]::Enter($scoutQueue.SyncRoot)
    try {
        if ($scoutQueue.Count -gt 10000) { throw 'EVENT_QUEUE_LIMIT' }
        for ($scoutIndex = 0; $scoutIndex -lt $scoutQueue.Count; $scoutIndex++) {
            $scoutCandidate = $scoutQueue[$scoutIndex]
            if ($scoutCandidate.SourceIdentifier -in $SourceIdentifiers) {
                $scoutPending.Add($scoutCandidate)
            }
        }
        return $scoutPending.ToArray()
    } finally { [Threading.Monitor]::Exit($scoutQueue.SyncRoot) }
}

function Acknowledge-ScoutQueuedEvent([System.Management.Automation.PSEventArgs]$QueuedEvent) {
    $scoutQueue = $ExecutionContext.Events.ReceivedEvents
    [Threading.Monitor]::Enter($scoutQueue.SyncRoot)
    try {
        for ($scoutIndex = 0; $scoutIndex -lt $scoutQueue.Count; $scoutIndex++) {
            if ([object]::ReferenceEquals($scoutQueue[$scoutIndex], $QueuedEvent)) {
                # Remove precisely the persisted object, including when another
                # queued object has the same numeric EventIdentifier.
                $scoutQueue.RemoveAt($scoutIndex)
                return
            }
        }
        throw 'QUEUED_EVENT_OBJECT_MISSING'
    } finally { [Threading.Monitor]::Exit($scoutQueue.SyncRoot) }
}
