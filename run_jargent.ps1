$ErrorActionPreference = "Stop"
$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "JARGENT is not set up yet. Run .\setup.ps1 first."
}

if ([string]::IsNullOrWhiteSpace($env:GROQ_API_KEY)) {
    $env:GROQ_API_KEY = [Environment]::GetEnvironmentVariable("GROQ_API_KEY", "User")
}

if ([string]::IsNullOrWhiteSpace($env:GROQ_API_KEY)) {
    throw "GROQ_API_KEY is missing. Run .\setup.ps1 again."
}

& $python (Join-Path $PSScriptRoot "jargent.py")
