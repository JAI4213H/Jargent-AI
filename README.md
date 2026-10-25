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

## Setup

1. Create a Python environment with the project dependencies.
2. Set the `GROQ_API_KEY` environment variable.
3. Keep the Piper voice model files in the project directory. They are intentionally not stored in Git.
4. Run:

```powershell
python jargent.py
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
