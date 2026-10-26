# JARGENT AI

![JARGENT AI](assets/jargent-hero.png)

JARGENT AI is a personal background computer operator for Windows.

Instead of only answering questions, JARGENT is being built to help manage everyday computer work: files, spreadsheets, images, documents, and repeatable workflows.

## What it can do now

The current prototype can:

- Accept voice input and produce voice output.
- Detect the wake word `Jargent`.
- Call tools through a Groq language model.
- Run Windows PowerShell commands.
- Inspect and edit Excel workbooks.
- Find spreadsheet columns without sending the whole workbook to the model.
- Analyze images and screenshots.
- Resize very small images before vision analysis.
- Move, copy, and rename files with basic verification.

## Example requests

```text
Jargent, describe this image.
Jargent, find the newest image in Downloads.
Jargent, add a Pass or Fail column using Marks / 100.
Jargent, organize my Downloads folder.
```

## How it works

```text
Voice or text
    ↓
Language model understands the request
    ↓
JARGENT selects a local tool
    ↓
The tool performs the operation
    ↓
The result is returned to the model
    ↓
JARGENT reports the result by text and voice
```

## Setup on another Windows laptop

Install Python 3.10 or newer, download this project, open PowerShell in its folder, and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup.ps1
```

The setup script installs the Python packages, downloads the Whisper and Piper voice models, asks for your Groq API key, and saves it only in your Windows user environment. The model files are downloaded locally and are not stored in Git.

Start JARGENT later with:

```powershell
.\run_jargent.ps1
```

If PowerShell blocks scripts, use:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

Say `Jargent` to activate voice input. Say `exit.` to save the current conversation and stop.

## Why JARGENT is different from Codex

Codex is primarily designed for software engineering: writing, debugging, reviewing, and shipping code.

JARGENT is designed for personal computer operations:

- Organizing files and folders.
- Working with spreadsheets and documents.
- Handling images and downloads.
- Running repeatable personal workflows.
- Using voice and background execution.
- Remembering personal preferences.
- Verifying changes and eventually supporting backups and undo.

The goal is not to make another coding agent. The goal is to build a reliable personal operator that completes digital work while the user continues using the computer.

## Project status

JARGENT is an early prototype. The tool-calling foundation is working, but the following product layers are still being built:

- Background task queue.
- Preview and confirmation flow.
- Backups and undo.
- Action history and audit records.
- Stronger permission boundaries.
- Cross-application workflows.

The long-term promise is simple:

> Tell JARGENT the outcome. It completes the work safely, verifies what changed, and explains the result.

## Privacy note

Do not commit API keys, personal conversation history, voice recordings, screenshots, or model weights. Local runtime files are excluded through `.gitignore`.
