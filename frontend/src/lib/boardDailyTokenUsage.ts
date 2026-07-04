export type DailyChartMode = "project_total";

type DailyProjectModelSegment = {
  model_key: string;
  model_label: string;
  tokens: number;
};

type DailyProjectDay = {
  date: string;
  tokens: number;
  models: DailyProjectModelSegment[];
};

type DailyTaskDay = {
  date: string;
  tokens: number;
  attribution: string;
};

type DailyTaskSeries = {
  task_id: string;
  task_title: string;
  status: string;
  attribution: string;
  days: DailyTaskDay[];
};

type DailyTokenUsage = {
  default_mode: string;
  project_days: DailyProjectDay[];
  tasks: DailyTaskSeries[];
  notes: string[];
  has_partial_data: boolean;
  has_task_links: boolean;
};

type ChartBar = {
  date: string;
  value: number;
  segments: { id: string; label: string; value: number }[];
};

type ChartSeries = {
  id: string;
  label: string;
  bars: ChartBar[];
};

type ChartLegendItem = {
  id: string;
  label: string;
};

function compareChartBarDates(left: ChartBar, right: ChartBar) {
  return left.date.localeCompare(right.date);
}

function sortBarsByDate(bars: ChartBar[]) {
  return [...bars].sort(compareChartBarDates);
}

function firstMeaningfulNote(notes: string[]) {
  return notes.map((note) => note.trim()).find(Boolean) ?? "";
}

export function buildDailyChartModel(
  daily: DailyTokenUsage | null,
  mode: DailyChartMode,
): { series: ChartSeries[]; legend: ChartLegendItem[]; supportingText: string } {
  if (!daily) {
    return { series: [], legend: [], supportingText: "Daily token usage unavailable." };
  }

  const supportingText = firstMeaningfulNote(daily.notes);
  const legendMap = new Map<string, ChartLegendItem>();
  const bars = sortBarsByDate(
    daily.project_days.map((day) => {
      const segments = day.models.map((segment) => {
        legendMap.set(segment.model_key, { id: segment.model_key, label: segment.model_label });
        return { id: segment.model_key, label: segment.model_label, value: segment.tokens };
      });
      return { date: day.date, value: day.tokens, segments };
    }),
  );
  return {
    series:
      mode === "project_total"
      ? [
          {
            id: "project_total",
            label: "Project total",
            bars,
          },
        ]
      : [],
    legend: [...legendMap.values()].sort((left, right) => left.label.toLowerCase().localeCompare(right.label.toLowerCase())),
    supportingText,
  };
}
