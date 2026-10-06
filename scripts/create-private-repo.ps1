param([string]$RepoName = "fundforge")
# Run locally after inspecting this script and authenticating with gh auth login.
$ErrorActionPreference = "Stop"

function Invoke-Git {
    param([string[]]$Arguments)
    & git @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Git failed: $($Arguments[0])" }
}

function Invoke-Probe {
    param([string]$Command, [string[]]$Arguments)
    # Expected nonzero exits must not become terminating stderr errors in PS 5.1.
    $ErrorActionPreference = 'Continue'
    & $Command @Arguments *> $null
    return $LASTEXITCODE
}

if ($RepoName -notmatch '^[A-Za-z0-9._-]+$') {
    throw "Repository name must use letters, numbers, dots, underscores or hyphens."
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "Install Git first." }
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw "Install GitHub CLI first, then run gh auth login." }
if ((Invoke-Probe -Command 'gh' -Arguments @('auth', 'status')) -ne 0) {
    throw "Run gh auth login first. Do not paste tokens into chat."
}

$PackageRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $PackageRoot
$ProfileText = & gh api user --jq '{login: .login, id: .id}'
if ($LASTEXITCODE -ne 0) { throw "Unable to resolve authenticated GitHub identity." }
$GitHubIdentity = ($ProfileText -join "`n") | ConvertFrom-Json
$Owner = $GitHubIdentity.login
if (-not $Owner -or -not $GitHubIdentity.id) { throw "Invalid authenticated GitHub identity." }

if ((Invoke-Probe -Command 'gh' -Arguments @('repo', 'view', "$Owner/$RepoName")) -eq 0) {
    throw "Repository $Owner/$RepoName already exists. Choose another name; nothing was overwritten."
}
if ((Invoke-Probe -Command 'git' -Arguments @('rev-parse', '--show-toplevel')) -eq 0) {
    $ExistingRoot = & git rev-parse --show-toplevel
    $ResolvedExistingRoot = (Resolve-Path ($ExistingRoot -join '')).Path
    if ($ResolvedExistingRoot -ne $PackageRoot) {
        throw "Package is inside another Git repository. Move it to a separate folder first."
    }
} else {
    Invoke-Git -Arguments @('init', '--initial-branch=main')
}
if ((Invoke-Probe -Command 'git' -Arguments @('remote', 'get-url', 'origin')) -eq 0) {
    throw "An origin already exists. This script does not replace remotes."
}
& git diff --cached --quiet
if ($LASTEXITCODE -ne 0) { throw "Existing staged changes detected. Resolve them first." }

$ExistingName = & git config user.name
if ($LASTEXITCODE -ne 0 -or -not $ExistingName) {
    Invoke-Git -Arguments @('config', '--local', 'user.name', $Owner)
}
$ExistingEmail = & git config user.email
if ($LASTEXITCODE -ne 0 -or -not $ExistingEmail) {
    $NoReply = "$($GitHubIdentity.id)+$Owner@users.noreply.github.com"
    Invoke-Git -Arguments @('config', '--local', 'user.email', $NoReply)
}

# Explicit package paths; do not stage an arbitrary personal resume or secret file.
Invoke-Git -Arguments @('add', '--', 'README.md', 'CLAUDE.md', '.gitignore', 'docs', 'fixtures', 'scripts', '.claude/agents')
& git diff --cached --quiet
if ($LASTEXITCODE -eq 1) {
    Invoke-Git -Arguments @('commit', '-m', 'docs: add FundForge specification and Claude handoff')
} elseif ($LASTEXITCODE -ne 0) {
    throw "Unable to inspect staged changes."
}
& gh repo create "$Owner/$RepoName" --private --source=. --remote=origin --push
if ($LASTEXITCODE -ne 0) { throw "GitHub creation/push failed. Inspect state; do not claim success." }
$ResultText = & gh repo view "$Owner/$RepoName" --json nameWithOwner,isPrivate,url
if ($LASTEXITCODE -ne 0) { throw "Remote verification failed." }
$RemoteResult = ($ResultText -join "`n") | ConvertFrom-Json
if (-not $RemoteResult.isPrivate) { throw "Privacy verification failed. No visibility change was attempted." }
$ResultText
