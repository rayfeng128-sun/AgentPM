import test from "node:test";
import assert from "node:assert/strict";

import { buildDailyChartModel } from "../../.test-dist/boardDailyTokenUsage.js";

const daily = {
  default_mode: "project_total",
  has_partial_data: false,
  has_task_links: true,
  notes: [],
  project_days: [
    {
      date: "2026-06-29",
      tokens: 600,
      models: [
        { model_key: "gpt-5.5", model_label: "gpt-5.5", tokens: 400 },
        { model_key: "deepseek", model_label: "DeepSeek", tokens: 200 },
      ],
    },
    {
      date: "2026-06-30",
      tokens: 900,
      models: [{ model_key: "gpt-5.4-mini", model_label: "gpt-5.4-mini", tokens: 900 }],
    },
  ],
  tasks: [
    {
      task_id: "alpha",
      task_title: "Alpha",
      status: "doing",
      attribution: "direct",
      days: [{ date: "2026-06-29", tokens: 600, attribution: "direct" }],
    },
    {
      task_id: "beta",
      task_title: "Beta",
      status: "blocked",
      attribution: "shared",
      days: [{ date: "2026-06-30", tokens: 900, attribution: "shared" }],
    },
  ],
};

test("builds project-total bars", () => {
  const model = buildDailyChartModel(daily, "project_total");
  assert.equal(model.series.length, 1);
  assert.equal(model.series[0]?.bars[0]?.date, "2026-06-29");
  assert.equal(model.series[0]?.bars[0]?.value, 600);
  assert.deepEqual(model.series[0]?.bars[0]?.segments, [
    { id: "gpt-5.5", label: "gpt-5.5", value: 400 },
    { id: "deepseek", label: "DeepSeek", value: 200 },
  ]);
});

test("keeps reconstructed project bars separate by day", () => {
  const model = buildDailyChartModel(
    {
      ...daily,
      project_days: [
        { date: "2026-06-29", tokens: 240, models: [{ model_key: "gpt-5.5", model_label: "gpt-5.5", tokens: 240 }] },
        { date: "2026-06-28", tokens: 120, models: [{ model_key: "unknown-model", model_label: "Unknown model", tokens: 120 }] },
      ],
    },
    "project_total",
  );

  assert.deepEqual(
    model.series[0]?.bars.map((bar) => ({ date: bar.date, value: bar.value })),
    [
      { date: "2026-06-28", value: 120 },
      { date: "2026-06-29", value: 240 },
    ],
  );
});

test("returns a flattened project legend from model segments", () => {
  const model = buildDailyChartModel(daily, "project_total");
  assert.deepEqual(model.legend, [
    { id: "deepseek", label: "DeepSeek" },
    { id: "gpt-5.4-mini", label: "gpt-5.4-mini" },
    { id: "gpt-5.5", label: "gpt-5.5" },
  ]);
});

test("returns reconstructed-history partial-data helper text", () => {
  const model = buildDailyChartModel(
    {
      ...daily,
      has_partial_data: true,
      notes: ["Some linked session totals could not be reconstructed from cumulative snapshots into daily history."],
    },
    "project_total",
  );
  assert.equal(model.supportingText, "Some linked session totals could not be reconstructed from cumulative snapshots into daily history.");
});

test("uses the first non-empty backend note", () => {
  const model = buildDailyChartModel(
    {
      ...daily,
      notes: ["", "   ", "Some linked session totals could not be reconstructed from cumulative snapshots into daily history."],
    },
    "project_total",
  );

  assert.equal(model.supportingText, "Some linked session totals could not be reconstructed from cumulative snapshots into daily history.");
});

test("preserves the backend-provided primary note without concatenating extra notes", () => {
  const model = buildDailyChartModel(
    {
      ...daily,
      notes: [
        "Some linked session totals could not be reconstructed from cumulative snapshots into daily history.",
        "Task-based daily views require linked Codex sessions.",
      ],
    },
    "project_total",
  );

  assert.equal(model.supportingText, "Some linked session totals could not be reconstructed from cumulative snapshots into daily history.");
});

test("sorts project bars chronologically", () => {
  const model = buildDailyChartModel(
    {
      ...daily,
      project_days: [
        { date: "2026-06-30", tokens: 300, models: [{ model_key: "a", model_label: "A", tokens: 300 }] },
        { date: "2026-06-28", tokens: 100, models: [{ model_key: "b", model_label: "B", tokens: 100 }] },
        { date: "2026-06-29", tokens: 200, models: [{ model_key: "c", model_label: "C", tokens: 200 }] },
      ],
    },
    "project_total",
  );

  assert.deepEqual(
    model.series[0]?.bars.map((bar) => ({ date: bar.date, value: bar.value })),
    [
      { date: "2026-06-28", value: 100 },
      { date: "2026-06-29", value: 200 },
      { date: "2026-06-30", value: 300 },
    ],
  );
});

test("surfaces backend note for project-total view", () => {
  const model = buildDailyChartModel(
    {
      default_mode: "project_total",
      project_days: [],
      tasks: [],
      notes: ["Some project session totals could not be reconstructed from cumulative snapshots into daily history."],
      has_partial_data: false,
      has_task_links: false,
    },
    "project_total",
  );

  assert.match(model.supportingText, /project session totals/);
});
