# N1 Windows owner checklist V001

Preparation only: **HOSTED_READINESS_BLOCKED**. No command in this document has
been run against Claude or an account during its preparation. This checklist
registers no consent and changes no N1 binding. Start point: main
`d27de49978dc32d5c8673a8e9b1de8b028f9b316`; PRs #11 and #13 are merged.
Their collector and V002 prompt implementation need no repetition. V002 is not
a prerequisite for N1; N1 retains its exact original fictional PLAIN-shaped input.

## 1. Owner: identify the installation without starting Claude

Run these in a normal PowerShell terminal. They inspect command resolution and
the chosen executable, not account/configuration files. No installation, update,
login, process termination or model query is included.

```powershell
$scoutClaudePaths = @(
    (Get-Command claude.exe -CommandType Application -All -ErrorAction SilentlyContinue).Source
    (Join-Path $env:USERPROFILE '.local\bin\claude.exe')
    (Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Packages\Anthropic.ClaudeCode_Microsoft.Winget.Source_8wekyb3d8bbwe\claude.exe')
) | Where-Object {
    $_ -and (Test-Path -LiteralPath $_ -PathType Leaf)
} | Select-Object -Unique

if (-not $scoutClaudePaths) {
    Write-Output 'No native Claude executable found in these locations.'
}
foreach ($scoutClaudePath in $scoutClaudePaths) {
    Get-Item -LiteralPath $scoutClaudePath |
        Select-Object FullName, Length, Attributes, LinkType, Target | Format-List
    Get-FileHash -LiteralPath $scoutClaudePath -Algorithm SHA256 | Format-List
    (Get-Item -LiteralPath $scoutClaudePath).VersionInfo |
        Select-Object FileVersion, ProductVersion | Format-List
}
Get-Command python -All -ErrorAction SilentlyContinue |
    Select-Object CommandType, Source | Format-List
[Environment]::OSVersion.Version
$PSVersionTable.PSVersion
```

The WinGet candidate is the exact location recorded in the existing V003 setup
documentation; discovery reads only the executable, never runs V003. These few
locations are not an exhaustive installation search. Select the actual native
`claude.exe` application path from the result. Do not
invoke an alias/function, npm `.cmd`/`.ps1` shim, WSL installation or an unresolved
link. Multiple installations require selecting exactly one, not deleting others.
If no native executable is found, report that and stop: installation or updating
would be a separate owner action with download/write/configuration risks.

No placeholder replacement is needed in this discovery block. Share selected path, SHA256
and version metadata; local user names in paths may be redacted in public reports
(the eventual private binding needs the exact path). These commands reveal local
paths and read executable bytes. A hash identifies bytes; it is not a trust or
compatibility certificate. File version metadata may be absent and is not a
substitute for an observed CLI version. Do not hash or send any account files.

Use native Windows for this package, not a WSL migration. Current official
[setup documentation](https://code.claude.com/docs/en/setup) lists native Windows
support and makes Git Bash optional. N1 disables tools; there is no reason to
install a shell tool solely for N1. That documentation also describes startup
auto-updates for native installations: recheck the exact executable hash before
every later approved command and stop on change. Do not silently disable updates
or add environment controls to the frozen runtime.

## 2. Owner: identify the local Python runtime

Choose the existing intended Python executable from step 1; do not install or
upgrade dependencies yet. For that executable only:

```powershell
$scoutPythonPaths = @(
    (Get-Command python.exe -CommandType Application -All -ErrorAction SilentlyContinue).Source |
        Where-Object { $_ -and $_ -notlike '*\Microsoft\WindowsApps\*' } |
        Select-Object -Unique
)
if ($scoutPythonPaths.Count -ne 1) {
    throw 'Expected one actual Python executable; report discovery results before proceeding.'
}
$scoutPythonExe = $scoutPythonPaths[0]
& $scoutPythonExe -I -c "import sys, platform, importlib.metadata as m; print(sys.executable); print(platform.python_version()); print({n:m.version(n) for n in ('jsonschema','referencing','jsonschema-specifications')})"
```

This starts Python, not Claude. Isolated mode avoids importing repository or
user-site modules; it reports installed distribution metadata and local paths.
A missing distribution is a setup finding, not permission to download it.
The final N1 binding must pin the actual Python/dependency versions. Windows CI
uses Python 3.13; CI success does not identify the owner's runtime. Use existing
local fixture tests to establish compatibility before registering execution.

## 3. Owner: supply setup facts, without inspecting credentials

From what you already know, state whether a dedicated research subscription is
already configured separately from development Claude, or whether this is unknown.
The intended child-only configuration is `%USERPROFILE%\.claude-research`;
changing a directory variable alone does not establish the account behind it.
Do not copy credentials, open configuration files, log in/out or alter global
environment variables to answer. If setup is absent or unknown, plan a separately
authorised owner-managed setup/identification step before the quiet baseline.

Choose a time when you can voluntarily pause development Claude terminals,
IDE integrations and background activity. Closing a visible terminal is not proof
that no separate process remains. Do not use broad process kills. Do not send a
full process command-line listing or environment dump.

## 4. Review a bounded administrative window before running any CLI command

Steps 1-3 require no Claude invocation. The following are **future command scopes,
not instructions to run now**:

| Exact command shape using the bound executable | What it can establish | Required boundary |
|---|---|---|
| `"<bound exe>" --version` | Installed CLI's reported version | Separate explicit administrative authorisation if existing evidence is insufficient |
| `"<bound exe>" --help` | Advertised flags for this build; not their effective behavior or hidden environment support | Separate explicit administrative authorisation if needed; unsupported/unverifiable controls STOP |
| `"<bound exe>" auth status` | Authentication/config-directory categories exposed by this build | The original proposal allows at most one separately approved owner-run command, 30-second watchdog, in its own monitored window |

The frozen N1 administrative allowance does **not** include help/version. If those
are necessary, review a separate, finite administrative scope before invocation;
do not expand the original protocol in place. No model prompt, `doctor`, install,
update, login, resume, config or fallback command is included. Documentation/help
is evidence of advertised support, not proof that all requested isolation/retry
controls are enforced. Record any unresolved control as unresolved, not supported.

Every approved administrative command needs the reviewed child-only allowlisted
research environment, sterile directory, pinned executable and its own monitored
window. Avoid a casual invocation from the shared IDE shell. Even administrative
startup may initialise/write state, check updates or contact services; do not
promise it is side-effect-free or network-free. No such command authorises a model
request. Stop on an unexpected prompt or account fallback. Raw auth output is
neither retained nor shared: the owner reports only approved config-directory and
authentication-method categories, with a separate private account attestation.

The official [CLI reference](https://code.claude.com/docs/en/cli-reference) says
`auth status` reports `configDirectory` starting at v2.1.268, and `--restricted`
requires v2.1.248+. These are documented minimums for those features, not a
certificate for the complete N1 argv. An older build or missing field means STOP
and review; never read credential contents to fill the gap. Canonical Opus ID,
subscription entitlement and Medium/32,768 support also need explicit evidence;
do not probe the model in advance of N1. Backend pinning remains limited.

## 5. Engineering: finish only the missing live admission and launch connection

**This is a real remaining engineering blocker, not an owner setting.**
`n1_collector/readiness.py:launch_native()` always refuses, and
`collector.py` permits only fixed Python fixtures. Supplying approval or installing
Claude cannot enable native execution. Existing review hashes check consistency;
they are not a live account observer.

After the executable/runtime facts are known, the narrow offline follow-up is one
Windows observer/admission connection and N1-only adapter reusing the existing
Capture, single-use registry and byte spool. Test it with local subprocess fixtures
only, and independently review it before use. Do not add a new scientific journal,
provider parser, campaign runner or replacement collector. A native launch must:

- Admit only the reviewed runtime, exact request/system/implementation and fresh
  sole reservation after actual immediate prelaunch observations.
- Observe the exact seven metadata paths in `v004_monitoring.ACCOUNT_PATHS`, with
  no content reads; >=60-second baseline and cooldown, gaps <=5 seconds, comparing
  against the original baseline throughout. Check managed-policy **presence** only
  under an agreed scope; unknown or present policy blocks this proposal.
- Establish existing-process identity plus reliable process-start/ancestry coverage
  on this Windows host. Polling alone misses transient processes. Prove the chosen
  observation mechanism with harmless local children and detect gaps/loss of
  coverage; do not infer coverage from an empty process list. Access denial means
  STOP, not automatic privilege escalation.
- Signal STOP/cancellation on any metadata drift (including research files),
  unexpected development Claude, account ambiguity, changed executable/binding,
  missing coverage, storage/journal fault or unresolved descendants/EOF. Retain
  evidence and consumed state; no retry, recovery or post-hoc whitelist.
- Revalidate mutable bindings immediately before the single spawn; retain existing
  600-second watchdog, 12-MiB recording trigger and bounded cancellation/drain.
  Process cancellation never proves remote cancellation. Windows job-assignment
  gaps and power-loss/local-filesystem limitations remain disclosed.

Actual Windows observer access/coverage, policy presence and account provenance
require an authorised local window. They cannot be established by fictional tests.
No historical writer attribution changes: it remains **UNKNOWN**; metadata drift
does not establish credential leakage. If legitimate startup writes fail the
zero-drift gate, preserve the stop and seek a prospective decision; do not rerun.

## 6. Owner: review and approve the complete bound package last

Only after steps 1-5 produce reviewable evidence: decide the exact canonical model,
runtime/collector hashes, sole reservation/registry/capture/session/sterile paths,
private access/retention arrangements and accepted local-filesystem threat model.
Then separately register named/date-stamped consent for the exact N1 package and
both seed IDs/text hashes. Explicitly adopt the N1-only hosted-use exception despite
the retained `approved_for_hosted_use:false` flags; never flip the flags. Neither
merged PRs nor this checklist supply that approval. No binding is filled here.

Accept or decline the disclosed resource/privacy limitations: R3 60,000 planning,
120,000 elevated, proposed 200,000 best-effort emergency; 32,768 candidate per
response; exact inclusive input/cache/output accounting with thinking counted
once. No token/financial guarantee or validated live native usage meter exists.
No unseen provider-request count, charge or remote cancellation is inferred.

## 7. One controlled N1 observation, only after explicit execution authorisation

Use the reviewed adapter, never an ad hoc PowerShell pipe. Deliver the unchanged
request bytes once then EOF; preserve stdout/stderr bytes privately without
decoding/reformatting. One parent maximum; at most two visible generations with
the second only evidenced append-only output-limit continuation. No repairs,
replacement, manual continuation, additional probe or automatic retry.

Native message/request IDs, event shapes, fragment/snapshot ordering, terminal
usage and continuation semantics are **UNKNOWN until this observation**. The byte
collector does not need an invented parser to capture them. After N1, STOP for
offline interpretation; an unobserved continuation branch remains unvalidated.
Successful fictional cards are not scientific findings. No V004 scientific slot,
Path B activation or further hosted call follows.

Immediate owner action: run steps 1-2 only, report those limited results plus the
already-known setup facts in step 3, and stop before any Claude/account command.
Those facts determine the smallest remaining adapter and administrative review.
V003, R2/R3, the full schema, experimental allocation, N1 inputs and all historical
records remain unchanged.

## Preparation verification

The unchanged proposal passed `prepare --check`; the three targeted proposal,
binding and readiness modules passed all 18 tests. Merged main's
[successful Windows CI](https://github.com/jarems421/ai-assisted-quantitative-research/actions/runs/39855108694)
reports 390 public, 264 Scout, six Scout process and 25 N1 process tests. That CI
certifies the tested local behavior, not native compatibility. This change adds
only this checklist; no production code, frozen artifact, approval or historical
record was changed. No Claude invocation, account inspection, consent registration
or hosted request occurred.

## Static follow-up on this workstation

The owner's PATH/default-location search found no executable. A subsequent static
check found the previously documented WinGet executable at
`C:\Users\runni\AppData\Local\Microsoft\WinGet\Packages\Anthropic.ClaudeCode_Microsoft.Winget.Source_8wekyb3d8bbwe\claude.exe`.
It is a regular file with no reported link target, 290,211,488 bytes; SHA256
`3ab075f78998efef8b87f491c2e4a39c309dddf44e51d0103eba4f3713d2a0ae`.
FileVersion and ProductVersion both report `2.1.302.0`. This is static executable
metadata, not an observed CLI version, compatibility result or registered binding.
No installation or PATH change is necessary for an absolute-path launch.

The existing Python resolved to
`C:\Users\runni\AppData\Local\Programs\Python\Python313\python.exe`:
Python `3.13.15`, jsonschema `4.26.0`, referencing `0.37.0`,
jsonschema-specifications `2025.9.1`, observed using isolated Python metadata only.
No Claude invocation or account inspection occurred. Steps 1-2 need no repetition
on this unchanged machine; the immediate owner input is step 3's already-known
research-setup facts. Fresh hashes/runtime verification remain required before
any separately approved invocation. All N1 execution bindings remain unset.
