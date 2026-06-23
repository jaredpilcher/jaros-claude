# Launch the jaros-claude REPL. Requires ANTHROPIC_API_KEY in the environment.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
if (-not $env:ANTHROPIC_API_KEY) {
  Write-Warning "ANTHROPIC_API_KEY is not set - model calls will fail (the control tests still run with 'python -m pytest -q')."
}
python -m harness.cli @args
