# AgentPM Bootstrap Setup Design

## Summary

This document defines the approved v1 design for a local AgentPM bootstrap script that prepares an existing Codex project for AgentPM. The script is intentionally narrow: it should help a user create the minimum AgentPM-facing project metadata without polluting the project's business-facing structure, source tree, or runtime configuration.

The script is run from AgentPM against a target project path. It is not embedded in the dashboard UI for v1.

## Design Brief

- Product area: AgentPM project onboarding
- Primary user: developer or project owner preparing a local Codex project for AgentPM
- Invocation model: local script run from AgentPM with a target project path
- Trust requirement: avoid silent overwrites and keep rollback practical
- Structural requirement: do not pollute the target project's business scenario

## Goals

- Make it easy to prepare a local Codex project for AgentPM from one guided command.
- Generate a valid starter `agentpm.yaml` for projects that do not already have one.
- Keep AgentPM operational metadata isolated from the target project's product code and business documentation.
- Handle existing `AGENTS.md`, `CODEX.md`, and `agentpm.yaml` conservatively through explicit interactive choices.
- Provide a reliable rollback path for files created or modified by the setup run.

## Non-Goals

- Modifying application source code, package manifests, build configuration, or runtime behavior in the target project.
- Inferring full milestone structure from a repository automatically.
- Editing business-facing product docs by default.
- Registering the project inside the AgentPM UI automatically.
- Solving every existing governance convention across arbitrary repositories.

## Approved Product Direction

The approved direction is a sidecar bootstrap model:

- run the script from AgentPM
- pass the target project path as an argument
- create `agentpm.yaml` at project root when needed
- keep AgentPM operational state inside a dedicated `.agentpm/` directory
- optionally create Codex-facing root files only when they are missing or when the user explicitly approves an update

This keeps the target repository usable as-is while still making the AgentPM integration discoverable and easy to reverse.

## File Strategy

### Root-Level Files

The script may manage only a very small root-level surface:

- `agentpm.yaml`
- `AGENTS.md`
- `CODEX.md`

These files are root-level because AgentPM or Codex naturally benefit from finding them there. No other business-facing docs should be created at root by default in v1.

### Sidecar Directory

The script should reserve `.agentpm/` for AgentPM-only setup artifacts, such as:

- setup manifests
- rollback metadata
- optional helper notes or generated templates that do not need to live in the project root

The `.agentpm/` directory is the main mechanism for preventing business-scenario pollution.

## Setup Flow

### Invocation

The v1 command is path-based and run from AgentPM. The user points the script at a target repository path.

### Inspection Phase

Before making changes, the script inspects the target project for:

- path validity
- Git repository presence
- existing `agentpm.yaml`
- existing `AGENTS.md`
- existing `CODEX.md`
- existing `.agentpm/`

### Planning Phase

The script then presents a concise setup plan showing:

- which files are missing
- which files could be created
- which existing files may be updated
- which items will be skipped unless the user approves them

### Write Phase

The script applies the approved changes only after inspection and interactive confirmation.

## Interactive Behavior

If `agentpm.yaml`, `AGENTS.md`, or `CODEX.md` already exists, the script should not overwrite silently.

For each existing managed file, the user should be prompted to choose among:

- skip
- update using the AgentPM template or managed section strategy
- cancel the setup run

The exact update mechanism may vary by file during implementation, but the user-facing rule is fixed: existing files require an explicit choice.

## Starter Content

### `agentpm.yaml`

The script should generate a minimal, valid starter file that includes:

- project name
- absolute project path
- one starter milestone
- one or more starter tasks using supported statuses

The generated content should be small and readable so users can adapt it manually after setup.

### `AGENTS.md` and `CODEX.md`

These files are optional helpers in v1, not mandatory setup prerequisites.

If created, they should be lightweight and AgentPM-specific:

- explain that the repository is prepared for AgentPM
- point to `agentpm.yaml`
- keep instructions concise
- avoid copying large governance frameworks into the target project

## Rollback Model

Rollback is a first-class requirement for this feature.

Each setup run should write a manifest under `.agentpm/` that records:

- setup run identifier
- timestamp
- target path
- files created
- files modified
- backup location for prior content of modified files

The script should provide a rollback mode that:

- deletes files it created during the selected setup run
- restores backed-up content for files it modified
- stops with a warning if a target file has changed since the setup run and cannot be safely restored automatically

This protects user trust and prevents rollback from erasing later manual edits.

## Safety Rules

- Never modify source code or dependency configuration in the target project.
- Never overwrite an existing managed file without explicit user confirmation.
- Prefer creating missing files over editing existing ones.
- Keep all setup bookkeeping inside `.agentpm/`.
- Fail clearly when the target path is invalid or not writable.

## Verification Expectations

Implementation should prove:

- the script can create a fresh `agentpm.yaml` in a target repository
- the script can create `.agentpm/` bookkeeping safely
- the script prompts instead of overwriting existing files
- rollback removes created files and restores modified files from backups
- rollback warns instead of clobbering newer user edits

## Why This Fits The Product

This design supports AgentPM's project-briefing model without expanding into repository scaffolding or business-process ownership. It helps users prepare better source data for AgentPM while respecting the target project's own structure, documentation style, and delivery context.
