param(
    [string]$Server = 'http://127.0.0.1:8000',
    [string]$Godot = 'godot_console.exe'
)

$ErrorActionPreference = 'Stop'
$projectPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'game'

# Refresh class registration and imported assets before running a fresh checkout.
& $Godot --headless --path $projectPath --editor --import
if ($LASTEXITCODE -ne 0) { throw 'Godot project import failed.' }

try {
    $health = Invoke-RestMethod "$($Server.TrimEnd('/'))/api/health" -TimeoutSec 5
    if (-not $health.ok) { throw 'Server is unhealthy.' }
} catch {
    Write-Warning "The game server at $Server is unavailable. Start it with docker compose up -d db api, or pass -Server with a running server URL."
}

& $Godot --path $projectPath -- "--server=$Server"
exit $LASTEXITCODE
