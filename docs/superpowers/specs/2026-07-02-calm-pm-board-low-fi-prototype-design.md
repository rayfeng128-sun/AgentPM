# Calm PM Board Low-Fi Prototype Design

## Summary

This document defines the approved low-fidelity prototype direction for Codex Project Board v0.2. It stays within the existing `Calm PM Review Board` product direction and refines the Board experience to better support daily token visibility without turning the dashboard into an analyst-heavy reporting surface.

The prototype is static, not interactive implementation work.

## Design Brief

- Product: Codex Project Board v0.2
- Source of truth: `docs/product/02-task-progress-token-analytics-prd.md`
- Prototype mode: static low-fidelity screens
- Visual direction: `Calm PM Review Board`
- Primary audience: project manager
- Key addition to emphasize: `Daily token usage` in the Board view

## Goals

- Keep the Board readable in one scan for a PM.
- Show progress, scope coverage, cost pressure, and risk in the right order.
- Elevate daily token usage as a first-class Board insight.
- Preserve task drill-down and missing-data trust signals without overwhelming the main screen.

## Non-Goals

- Starting implementation or coding.
- Producing a high-fidelity visual design.
- Turning the Board into a token-analysis-first reporting surface.
- Exposing raw Codex transcript content.

## Screen Set

The approved prototype set contains three screens:

1. Main Board dashboard
2. Task detail drawer
3. Board state variations

This gives enough fidelity to validate hierarchy, drill-down, and trust states without multiplying screens unnecessarily.

## Main Board Dashboard

### Chosen Direction

The approved main screen is the refined `Option B` direction:

- reduced summary layer
- stronger daily trend surface
- calmer work area beneath

### Layout Hierarchy

#### Layer 1: Project Context

Top header content:

- project name
- local path
- Git branch
- last Codex activity
- refresh action
- data confidence signal

Left-side navigation remains project-oriented and stable:

- project list
- selected project status
- Board-first navigation

#### Layer 2: Three Summary Cards

Replace the denser four-card summary row with three stronger cards:

1. `Delivery health`
   Includes completion percentage, blocked count, and milestone pulse.
2. `Scope coverage`
   Includes PRD-linked versus unlinked work.
3. `Cost + attention`
   Includes total token pressure, over-budget tasks, and shared-attribution warnings.

This reduces top-layer noise and makes the first scan more decisive.

#### Layer 3: Primary Analytical Surface

The `Daily token usage` card becomes the main analytical surface of the Board.

Placement:

- directly below the summary cards
- visually larger than the summary cards
- paired with the attention queue

Card behavior:

- default mode: `Project total by day`
- secondary modes available in-card: `By task` and `Selected task`
- trend visibility is prioritized over dense breakdown

Adjacent support:

- an `Attention queue` sits beside the trend card
- it surfaces blocked work, unlinked scope, over-budget tasks, and attribution warnings

#### Layer 4: Deeper Work Surface

Below the trend layer, the Board shows:

- milestone progress
- task progress table

This area is still important, but it is intentionally not the first-scan layer.

## Task Detail Drawer

### Chosen Direction

The approved drawer direction is `Executive Drawer`, not `Analyst Drawer`.

### Drawer Purpose

The drawer helps a PM confirm:

- what the task is
- whether it is in planned scope
- what it cost
- whether it is risky
- what to do next

### Drawer Structure

Top summary:

- task title
- task ID
- task status
- milestone

Section 1: PRD association

- primary PRD reference
- additional PRD references when present
- scope state such as linked or unlinked

Section 2: token and attribution summary

- total tokens
- token budget state
- model label
- attribution state

Section 3: linked sessions

- session title or ID
- date
- model
- token total

Section 4: PM action framing

- key warning or risk note
- clear next-action suggestion

### Drawer Principle

Session detail is visible, but not allowed to dominate the drawer. The drawer remains PM-first rather than becoming an operator console.

## Board State Variations

### Chosen Direction

The approved direction is `Inline Calm States`.

### State Principle

The Board should remain structurally stable when data is partial or unavailable. Missing data should be explained inside the affected card or area instead of replacing the experience with large disruptive empty-state panels.

### Required States

The prototype must cover:

- partial daily data
- no task links
- shared attribution
- token data unavailable

### State Behavior

#### Partial Daily Data

- keep the daily chart visible
- show a short note that some session totals could not be placed on a day

#### No Task Links

- allow project-level token visibility when possible
- explain that task-oriented daily views require linked task sessions

#### Shared Attribution

- keep the chart usable
- label task-oriented values as shared rather than exclusive

#### Token Data Unavailable

- keep the Board structure intact
- show a concise explanation in the token area rather than removing the Board section entirely

## Why This Fits The PRD

This prototype direction aligns with the PRD because it:

- preserves project-manager-first visibility
- keeps task progress and PRD traceability in view
- adds a clearer daily token usage story to the Board
- supports task drill-down without requiring a context switch
- avoids inventing false precision when token attribution or day-level placement is incomplete

## Prototype Deliverable

The low-fi prototype should communicate:

- the reading order of the Board
- the prominence of daily token usage
- the calmer three-card summary layer
- the compact PM-first drawer
- the inline handling of missing or partial data

It does not need to prove production styling, final spacing, or coded interaction.

