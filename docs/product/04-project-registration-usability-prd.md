# Codex Project Board v0.3 PRD: Project Registration Usability

## 1. Product Summary

Codex Project Board v0.3 improves the project registration and project list management experience.

The current flow requires the user to manually type an absolute local path. This is slow and error-prone, especially for project managers or non-technical users. v0.3 replaces that with a guided project path selection dialog, automatically suggests a project name from the selected folder, and lets users remove projects from the sidebar list.

The product goal is to help the user answer:

```text
How can I add and manage monitored projects without manually typing filesystem paths?
```

## 2. Target User

Primary user:

- A project manager who monitors multiple Codex-assisted local projects and needs a simple way to add, identify, and remove projects from the dashboard.

Secondary user:

- A developer or agentic worker who frequently switches between local repositories and wants project setup to be fast and less error-prone.

## 3. User Stories

### Story 1: Select Project Path From A Dialog

As a project manager adding a monitored project,
in the context of a local dashboard,
I want to choose the project folder from a pop-up path selector,
so that I do not need to manually type or paste an absolute path.

Acceptance:

- The add-project flow opens a modal dialog.
- The dialog lets the user browse or select a local directory path.
- The selected path is shown before the project is added.
- The user can cancel without changing the project list.
- Invalid or inaccessible paths show a clear validation message.

### Story 2: Default Project Name From Folder Name

As a project manager adding a project,
in the context of selecting a local project directory,
I want the project name to default to the last folder name,
so that the form is prefilled with a sensible name.

Acceptance:

- When a path is selected, the project name field is filled with the last folder segment.
- Example: `/Users/ray/BaiduNetDisk/Project/AgentPM` defaults to `AgentPM`.
- The user can edit the default name before saving.
- If the selected path ends with a trailing slash, the default still uses the final folder name.
- If the user has already manually edited the project name, selecting a different path should ask before replacing the name or preserve the manual value.

### Story 3: Remove Project From List

As a project manager managing monitored projects,
in the context of the project sidebar,
I want an option button on each project item that lets me remove a project from the list,
so that stale or unwanted projects no longer clutter the dashboard.

Acceptance:

- Each project row in the project list has an option button.
- The option menu includes `Remove from list`.
- Removing a project asks for confirmation.
- Removing a project deletes only the dashboard registration, not the local project folder.
- If the removed project is currently selected, the UI returns to an empty or first-available project state.
- Removing a project refreshes the sidebar without requiring a page reload.

## 4. Scope

v0.3 includes:

- Add-project modal dialog.
- Project path picker or directory browser UI.
- Default project name derived from the selected directory basename.
- Editable project name field.
- Project list option menu.
- Remove-project confirmation dialog.
- Backend support for deleting a registered project.
- Backend support for project path selection if browser-only APIs are insufficient.

## 5. Non-Goals

v0.3 does not include:

- Deleting local project files.
- Renaming local project folders.
- Editing existing project paths after creation.
- Bulk project import.
- Cloud project discovery.
- Permission management beyond local filesystem access handled by the app/runtime.
- Remote team project administration.

## 6. Path Selection Design

### Recommended Approach

Use a local backend-assisted directory browser for v0.3.

Reason:

- Standard web pages cannot reliably access arbitrary local absolute paths through a custom file picker.
- Browser directory picker APIs can expose files, but support and absolute-path behavior vary.
- This product already runs as a local app with a backend that validates project paths, so backend-assisted directory browsing is the most predictable path.

### Path Selection Modal

Modal title:

```text
Add project
```

Fields and controls:

| UI Element | Behavior |
|---|---|
| Current directory breadcrumb | Shows the directory currently being browsed. |
| Directory list | Shows child folders user can open. |
| Path field | Shows selected absolute path; read-only by default. |
| Project name field | Defaults from selected folder name; editable. |
| Select folder button | Confirms the highlighted folder as project path. |
| Add project button | Creates or updates project registration. |
| Cancel button | Closes modal without changes. |

Suggested start locations:

- User home directory.
- Current AgentPM workspace.
- Recent registered project parent directories.

Backend directory browsing rules:

- Directory listing returns folders only.
- Hidden folders may be hidden by default, with an optional show-hidden toggle.
- Permission errors return a friendly unavailable message.
- The backend must not create, move, rename, or delete folders during browsing.
- The backend should normalize `~` and resolve selected paths before registration.

## 7. Project Name Defaulting Rules

Default name algorithm:

```text
default project name = basename(normalized selected path)
```

Examples:

| Selected path | Default name |
|---|---|
| `/Users/ray/BaiduNetDisk/Project/AgentPM` | `AgentPM` |
| `/Users/ray/BaiduNetDisk/Project/ExamSystem_2/` | `ExamSystem_2` |
| `/Users/ray/BaiduNetDisk/Obsidian/myObsVault` | `myObsVault` |

Rules:

- Path normalization removes trailing slashes before reading the basename.
- If basename is empty, keep the project name empty and show validation.
- The default name should be applied when a folder is selected.
- The user can edit the field after the default is applied.
- If the name field has been manually edited, changing the selected folder should preserve the edited name unless the user clears it.

## 8. Remove Project Design

### Project Row Option Menu

Each project row includes a compact option button.

Menu items:

| Item | Behavior |
|---|---|
| Remove from list | Opens confirmation dialog. |

Future menu items may include rename, reveal in finder, or refresh, but they are out of scope for v0.3.

### Confirmation Dialog

Title:

```text
Remove project from list?
```

Body:

```text
This removes the project from Codex Project Board only. It will not delete local files.
```

Actions:

- `Cancel`
- `Remove`

Behavior:

- `Cancel` closes the dialog.
- `Remove` deletes the project registration.
- If deletion fails, show an inline error and keep the project row.

## 9. API Requirements

Add endpoints:

```http
GET /api/filesystem/directories
DELETE /api/projects/{project_id}
```

### `GET /api/filesystem/directories`

Purpose:

- Return child directories for the path selector modal.

Query:

```http
GET /api/filesystem/directories?path=/Users/ray/BaiduNetDisk/Project
```

Response:

```json
{
  "path": "/Users/ray/BaiduNetDisk/Project",
  "parent": "/Users/ray/BaiduNetDisk",
  "entries": [
    {
      "name": "AgentPM",
      "path": "/Users/ray/BaiduNetDisk/Project/AgentPM",
      "is_directory": true,
      "readable": true
    }
  ],
  "error": null
}
```

Rules:

- Missing path defaults to the user's home directory.
- Inaccessible paths return `error` with an empty `entries` list.
- The endpoint should return directories only.
- The endpoint must not expose file contents.

### `DELETE /api/projects/{project_id}`

Purpose:

- Remove a project registration from the dashboard.

Response:

```json
{
  "removed": true,
  "project_id": "agentpm"
}
```

Rules:

- Unknown project returns 404.
- The endpoint deletes only the app database row.
- The endpoint must not delete or mutate local project files.

## 10. UI Requirements

### Add Project Flow

Default flow:

1. User selects `Add project`.
2. Modal opens.
3. User browses directories.
4. User selects a project folder.
5. Project name defaults from folder basename.
6. User edits name if needed.
7. User selects `Add project`.
8. Project appears in the sidebar and becomes selected.

Validation:

- No selected path: disable `Add project`.
- Empty project name: show `Project name is required`.
- Path does not exist: show `Project path does not exist`.
- Backend unavailable: show `Cannot browse local folders right now`.

### Project List Remove Flow

Default flow:

1. User opens option menu on project row.
2. User selects `Remove from list`.
3. Confirmation dialog opens.
4. User confirms.
5. Project is removed from sidebar.
6. If it was selected, the dashboard clears selection or selects the next project.

## 11. Edge Cases

| Case | Expected behavior |
|---|---|
| User selects folder with no `agentpm.yaml` | Project can be added; dashboard shows missing-plan warning. |
| User selects non-Git folder | Project can be added; dashboard shows Git unavailable. |
| User lacks permission to open a folder | Directory browser shows inaccessible state. |
| User removes currently selected project | Selection resets to no project or next project. |
| User cancels add modal | No project is created. |
| User cancels remove confirmation | Project remains. |
| Duplicate path is added | Existing registration is updated or replaced according to v0.1 rules. |

## 12. Acceptance Criteria

The v0.3 feature is acceptable when:

- The user can open an add-project modal from the project list.
- The user can select a local project directory without manually typing the absolute path.
- The selected path is visible before saving.
- The default project name is derived from the selected folder name.
- The project name remains editable.
- The user can remove a project from the project list through an option menu.
- Removing a project never deletes local files.
- Add, cancel, validation error, remove, and remove-cancel states work without page reload.
- Existing v0.1 and v0.2 dashboard behavior remains available.

## 13. Verification Plan

Backend verification:

- Unit test directory listing with a temporary folder tree.
- Unit test inaccessible or missing path response.
- Unit test delete existing project.
- Unit test delete unknown project returns 404.
- Unit test delete does not touch local project files.

Frontend verification:

- Add-project modal opens and closes.
- Directory selector populates from backend response.
- Selecting `/a/b/AgentPM` defaults project name to `AgentPM`.
- Editing project name is preserved before save.
- Add project creates the project and selects it.
- Project row option menu opens.
- Remove confirmation cancel leaves project untouched.
- Remove confirmation success removes project from sidebar.

Manual smoke test:

- Add `/Users/ray/BaiduNetDisk/Project/AgentPM` through the modal.
- Confirm default name is `AgentPM`.
- Remove it from the sidebar.
- Confirm the local folder still exists.
