$ErrorActionPreference = "Stop"

$project = $PSScriptRoot
$venv = Join-Path $project ".venv"
$python = Join-Path $venv "Scripts\python.exe"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python 3.10+ is required. Install Python and run this script again."
}

$pythonVersion = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$parts = $pythonVersion.Split('.')
if ([int]$parts[0] -lt 3 -or ([int]$parts[0] -eq 3 -and [int]$parts[1] -lt 10)) {
    throw "Python 3.10 or newer is required. Found Python $pythonVersion."
}

if (-not (Test-Path $python)) {
    Write-Host "Creating virtual environment..."
    python -m venv $venv
}

Write-Host "Installing Python packages..."
& $python -m pip install --upgrade pip
& $python -m pip install -r (Join-Path $project "requirements.txt")

$modelUrl = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
$configUrl = "$modelUrl.json"
$modelPath = Join-Path $project "en_US-lessac-medium.onnx"
$configPath = Join-Path $project "en_US-lessac-medium.onnx.json"

if (-not (Test-Path $modelPath)) {
    Write-Host "Downloading Piper voice model..."
    Invoke-WebRequest -Uri $modelUrl -OutFile $modelPath
}

if (-not (Test-Path $configPath)) {
    Write-Host "Downloading Piper voice configuration..."
    Invoke-WebRequest -Uri $configUrl -OutFile $configPath
}

Write-Host "Downloading the Whisper speech model..."
& $python -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8')"

$apiKey = [Environment]::GetEnvironmentVariable("GROQ_API_KEY", "User")
if ([string]::IsNullOrWhiteSpace($apiKey)) {
    $secure = Read-Host "Enter your Groq API key (input is hidden)" -AsSecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        $apiKey = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    }
    [Environment]::SetEnvironmentVariable("GROQ_API_KEY", $apiKey, "User")
}

New-Item -ItemType Directory -Force (Join-Path $project "voice_notes") | Out-Null
Write-Host "Setup complete. Start JARGENT with: .\run_jargent.ps1"
