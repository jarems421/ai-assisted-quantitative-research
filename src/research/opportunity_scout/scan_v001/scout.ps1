<#
Opportunity Scout one-command operator (SCOUT_SCAN_V001).

  .\scout.ps1 -SetGeminiKey               store the Gemini API key once, DPAPI-encrypted for this Windows user
  .\scout.ps1                             plan a new scan with the configured defaults, check, confirm, run once
  .\scout.ps1 -Count 2 -Budget 1          the same with explicit hypotheses and Gemini reservation cap (USD)
  .\scout.ps1 -Archive <plan> [-PlanOnly] use an existing unclaimed plan (for example Pilot 002)
  .\scout.ps1 ... -Confirm <plan sha256>  non-interactive confirmation of that exact plan

The key is never written to a script, an argument, an archive or the console. It is decrypted only into this
process's GEMINI_API_KEY for the duration of the Python call and removed afterwards.
#>
[CmdletBinding()]
param(
    [int]$Count,
    [double]$Budget,
    [string]$Archive,
    [string]$Confirm,
    [switch]$PlanOnly,
    [switch]$Json,
    [switch]$SetGeminiKey
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
$keyFile = Join-Path $env:LOCALAPPDATA 'ResearchOS\gemini-api-key.dpapi'

if ($SetGeminiKey) {
    $secure = Read-Host 'Gemini API key (input hidden)' -AsSecureString
    New-Item -ItemType Directory -Force -Path (Split-Path $keyFile) | Out-Null
    ConvertFrom-SecureString -SecureString $secure | Set-Content -Path $keyFile -Encoding ascii
    Write-Host "Stored, encrypted for this Windows user only: $keyFile"
    return
}

$pyArgs = @('-m', 'src.research.opportunity_scout.scan_v001', 'scan')
if ($PSBoundParameters.ContainsKey('Count')) { $pyArgs += @('--count', "$Count") }
if ($PSBoundParameters.ContainsKey('Budget')) { $pyArgs += @('--budget', "$Budget") }
if ($Archive) { $pyArgs += @('--archive', $Archive) }
if ($Confirm) { $pyArgs += @('--confirm', $Confirm) }
if ($PlanOnly) { $pyArgs += '--plan-only' }
if ($Json) { $pyArgs += '--json' }

$hadKey = Test-Path Env:GEMINI_API_KEY
$code = 2
try {
    if (-not $hadKey -and (Test-Path $keyFile)) {
        $secure = Get-Content -Path $keyFile | ConvertTo-SecureString
        $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
        try { $env:GEMINI_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
        finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
    }
    Push-Location $repo
    try { & python @pyArgs; $code = $LASTEXITCODE } finally { Pop-Location }
}
finally {
    if (-not $hadKey) { Remove-Item Env:GEMINI_API_KEY -ErrorAction SilentlyContinue }
}
exit $code
