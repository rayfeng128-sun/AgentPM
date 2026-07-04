# Board Daily Token Usage Design

## Summary

Add a `Daily token usage` card to the Board view so the dashboard can show token activity over time without leaving the project overview. The card should use a single `Project total by day` view with each daily column stacked by contributing model.

This feature extends the existing Board token analytics instead of creating a separate page or route.

## Goals

- Make daily token usage visible in the Board overview.
- Preserve the Board as a PM-first summary surface.
- Reuse the existing session attribution and model metadata already available in the backend.

## Non-Goals

- Creating a new token analytics page for this feature.
- Inventing daily values for sessions that do not have a reliable day.
- Splitting shared session totals into exclusive per-task values.
- Adding billing-grade cost calculation or new transcript exposure.

## Board Experience

### Placement

Add a new `Daily token usage` card near the existing token summary area in the Board tab.

### Default Mode

The default mode is `Project total by day`.

Behavior:

- Show one vertical bar per calendar day.
- Use the currently selected project and existing Board filters or context.
- Keep the chart visible even when partial data is missing.

### Chart Behavior

- One bar per day.
- Each bar shows summed attributable project tokens for that day.
- Each bar is visually stacked by model so the model mix is visible inside the total.
- The card keeps a compact `Project total` control for consistency, but does not expose task-view switching inside the Board chart.
- Include a small legend for the model colors used in the chart.

## Data Design

### Backend Shape

Extend the existing briefing response with a `daily_token_usage` payload that supports the project-wide Board chart and can carry per-day model segmentation.

Recommended payload structure:

- project-level daily totals
- project-level per-model daily segments
- metadata about missing or excluded sessions
- attribution notes required by the UI

This should remain part of the existing Board/briefing response unless implementation discovers a clear performance problem.

### Daily Grouping

- Group data by calendar day from rollout token timeline events, not only from the final session timestamp.
- Treat rollout `token_count` values as cumulative snapshots and derive each day's usage from the incremental growth between successive usable snapshots.
- Assign each incremental token delta to the calendar day of the later snapshot in that pair.
- Resolve the calendar day in the session's recorded local timezone when the rollout provides one; otherwise fall back to UTC.
- Use only positive deltas from snapshots with usable timestamps and token totals.
- If a session has tokens but no usable timeline for daily reconstruction, exclude it from day buckets and surface that omission in metadata rather than inventing daily history.
- If a session has tokens and a reliable session date but no reconstructable daily timeline, it may still contribute to non-daily token summaries while remaining excluded from the daily chart.

### Attribution Rules

- `Project total` sums all reconstructable per-day token deltas across project sessions for the current project path.
- Each model segment within a day inherits the daily deltas from sessions attributed to that model.
- If a session has no resolved model name, place its contribution into `Unknown model`.
- The implementation must avoid double counting within a single session by never summing multiple cumulative snapshots directly.

## States And Messaging

### Complete Data

- Render the chart normally.
- No warning copy is needed.

### Partial Daily Data

- Render the chart with available points.
- Show short supporting text such as `Some session totals could not be reconstructed into daily history.`

### No Daily Data

- Keep the card visible.
- Replace the chart with an empty state that explains why daily token usage is unavailable.

## Interaction Notes

- The card should feel like part of the Board summary rather than a standalone analytics module.
- Empty and partial states should be explicit, calm, and non-alarming.

## Prototype Fit

The current v0.2 prototype is strong on PM readability and task-level comparison, especially the summary cards, task table, and horizontal task token chart. The gap is temporal visibility: it shows which tasks are expensive, but not when token usage spikes happened or how activity changed day to day.

This daily token usage card fits the prototype direction because it:

- keeps charts supportive rather than dominant
- adds trend visibility to the Board instead of replacing task comparison
- creates a natural bridge from project overview to task drill-down

This change should complement the existing prototype rather than displace the horizontal task token chart defined for deeper task analytics.

## Verification

Verification should prove:

- backend reconstruction of daily token deltas from cumulative rollout snapshots
- correct project-total daily aggregation
- correct per-model segmentation within each project day
- handling of sessions with missing or incomplete daily timelines
- frontend rendering for populated, partial, and empty states

## Implementation Notes

- Prefer extending current backend token analytics models over introducing parallel chart-only models.
- Prefer a lightweight native chart implementation that matches the existing frontend stack unless the project already adopts a chart library during implementation.
- Keep the Board card compact and readable on desktop and mobile.
