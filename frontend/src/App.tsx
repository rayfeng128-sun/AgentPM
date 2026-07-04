import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  CalendarRange,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  CircleSlash,
  Clock3,
  FileText,
  Filter,
  FolderKanban,
  FolderPlus,
  GitBranch,
  LayoutGrid,
  Loader2,
  PanelsTopLeft,
  Plus,
  RefreshCw,
  ServerCrash,
  Settings,
  StepBack,
  Trash2,
  Users,
  Wallet,
  X,
} from "lucide-react";
import { buildDailyChartModel, type DailyChartMode } from "./lib/boardDailyTokenUsage";

type BriefingStatus = "active" | "idle" | "blocked" | "tests_failing" | "missing_plan" | "unknown";
type AlertLevel = "info" | "warning" | "error";
type TaskStatus = "todo" | "doing" | "done" | "blocked";
type AttributionState = "direct" | "shared" | "none" | "unavailable";
type StatusFilter = "all" | TaskStatus;
type PrdFilter = "all" | "linked" | "unlinked";
type TokenFilter = "all" | "over-budget" | "no-data" | "shared";
type WorkspaceTab = "board" | "prd" | "tasks" | "milestones" | "sessions" | "reports" | "settings";

type Project = {
  id: string;
  name: string;
  path: string;
  has_plan: boolean;
  is_git_repo: boolean;
};

type DirectoryRoot = {
  label: string;
  path: string;
};

type DirectoryOption = {
  name: string;
  path: string;
};

type DirectoryBrowseResponse = {
  current_path: string | null;
  parent_path: string | null;
  roots: DirectoryRoot[];
  directories: DirectoryOption[];
};

type ProgressSummary = {
  done: number | null;
  total: number | null;
  blocked: number | null;
  percent: number | null;
};

type TaskPlanItem = {
  id: string;
  title: string;
  status: TaskStatus;
  assignee: string | null;
  created_at: string | null;
  updated_at: string | null;
  session_note: string | null;
  user_story: string | null;
  scope: string | null;
  acceptance_criteria: string | null;
  verification_method: string | null;
  prd_refs: string[];
  codex_sessions: string[];
  token_budget: number | null;
};

type Milestone = {
  id: string;
  title: string;
  progress: ProgressSummary | null;
  tasks: TaskPlanItem[];
};

type TaskPlan = {
  project_id: string;
  progress: ProgressSummary;
  milestones: Milestone[];
  alerts: Alert[];
};

type CodexSession = {
  id: string;
  title: string;
  cwd: string;
  model: string | null;
  model_provider: string | null;
  tokens_used: number;
  updated_at_ms: number | null;
  rollout_path: string | null;
};

type TokenSummary = {
  total: number | null;
  recent_session: number | null;
  unavailable: boolean;
};

type GitState = {
  is_repo: boolean;
  branch: string | null;
  dirty_files: number;
  latest_commit: string | null;
  dirty_file_names: string[];
  unavailable: boolean;
};

type TestState = {
  status: "unknown" | "passing" | "failing";
  confidence: "low" | "high";
};

type Alert = {
  level: AlertLevel;
  message: string;
};

type TaskTokenSession = {
  id: string;
  title: string | null;
  model: string | null;
  model_provider: string | null;
  updated_at_ms: number | null;
  tokens: number | null;
  source: string;
  missing: boolean;
};

type TaskTokenUsageItem = {
  task_id: string;
  task_title: string;
  status: TaskStatus;
  prd_refs: string[];
  codex_sessions: string[];
  total_tokens: number | null;
  model_label: string;
  models: string[];
  model_providers: string[];
  input_tokens: number | null;
  cached_input_tokens: number | null;
  output_tokens: number | null;
  reasoning_output_tokens: number | null;
  token_budget: number | null;
  attribution: AttributionState;
  sessions: TaskTokenSession[];
  missing_sessions: string[];
  alerts: Alert[];
};

type TaskTokenUsage = {
  project_id: string;
  tasks: TaskTokenUsageItem[];
  alerts: Alert[];
};

type DailyTokenProjectDay = {
  date: string;
  tokens: number;
  models: { model_key: string; model_label: string; tokens: number }[];
};

type DailyTokenTaskDay = {
  date: string;
  tokens: number;
  attribution: AttributionState;
};

type DailyTokenTaskSeries = {
  task_id: string;
  task_title: string;
  status: TaskStatus;
  attribution: AttributionState;
  days: DailyTokenTaskDay[];
};

type DailyTokenUsage = {
  default_mode: DailyChartMode;
  project_days: DailyTokenProjectDay[];
  tasks: DailyTokenTaskSeries[];
  notes: string[];
  has_partial_data: boolean;
  has_task_links: boolean;
};

type BriefingResponse = {
  project: Project;
  progress: ProgressSummary;
  briefing: {
    status: BriefingStatus;
    summary: string;
    next_action: string;
  };
  tokens: TokenSummary;
  git: GitState;
  test: TestState;
  sessions: CodexSession[];
  alerts: Alert[];
  task_plan: TaskPlan | null;
  task_token_usage: TaskTokenUsage | null;
  daily_token_usage: DailyTokenUsage | null;
};

type PrdDocumentResponse = {
  ref: string;
  path: string;
  anchor: string | null;
  title: string | null;
  content: string;
  unavailable: boolean;
};

type TaskView = TaskPlanItem &
  Pick<
    TaskTokenUsageItem,
    | "total_tokens"
    | "model_label"
    | "models"
    | "model_providers"
    | "input_tokens"
    | "cached_input_tokens"
    | "output_tokens"
    | "reasoning_output_tokens"
    | "token_budget"
    | "attribution"
    | "sessions"
    | "missing_sessions"
    | "alerts"
  > & {
    milestone_id: string;
    milestone_title: string;
    milestone_index: number;
    task_index: number;
  };

type CoverageRow = {
  ref: string;
  required: number;
  covered: number;
  coverage: number;
  tokens: number;
  attention: string;
};

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

const mainNav = [
  { id: "overview", label: "Overview", icon: LayoutGrid },
  { id: "projects", label: "Projects", icon: FolderKanban, active: true },
  { id: "prd-library", label: "PRD Library", icon: FileText },
  { id: "codex-sessions", label: "Codex Sessions", icon: PanelsTopLeft },
  { id: "reports", label: "Reports", icon: BarChart3 },
  { id: "teams", label: "Teams", icon: Users },
  { id: "settings", label: "Settings", icon: Settings },
] as const;

const workspaceTabs: { id: WorkspaceTab; label: string }[] = [
  { id: "board", label: "Board" },
  { id: "prd", label: "PRD" },
  { id: "tasks", label: "Tasks" },
  { id: "milestones", label: "Milestones" },
  { id: "sessions", label: "Sessions" },
  { id: "reports", label: "Reports" },
  { id: "settings", label: "Settings" },
];

const statusCopy: Record<BriefingStatus, string> = {
  active: "Active",
  idle: "Idle",
  blocked: "Blocked",
  tests_failing: "Tests failing",
  missing_plan: "Plan unavailable",
  unknown: "Unknown",
};

const statusIcon: Record<BriefingStatus, typeof Activity> = {
  active: Activity,
  idle: Clock3,
  blocked: CircleSlash,
  tests_failing: AlertTriangle,
  missing_plan: FolderPlus,
  unknown: ServerCrash,
};

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      message = typeof body.detail === "string" ? body.detail : message;
    } catch {
      // Ignore invalid error body.
    }
    throw new Error(message);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

function compactTokens(value: number | null) {
  if (value === null) return "No data";
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(value >= 10_000_000 ? 0 : 1)}M`;
  if (value >= 1_000) return `${Math.round(value / 1_000)}K`;
  return value.toLocaleString();
}

function numberLabel(value: number | null, fallback = "Unavailable") {
  return value === null ? fallback : value.toLocaleString();
}

function formatShortDay(value: string) {
  const parsed = new Date(`${value}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) return value.slice(5);
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(parsed);
}

function shortenModelList(task: Pick<TaskView, "models" | "model_label">) {
  if (task.models.length) return task.models.join(", ");
  return modelLabel(task);
}

function providerLabel(provider: string) {
  if (provider.toLowerCase() === "openai") return "OpenAI";
  return `${provider[0].toUpperCase()}${provider.slice(1)}`;
}

function statusTone(status: TaskStatus) {
  if (status === "done") return "done";
  if (status === "doing") return "doing";
  if (status === "blocked") return "blocked";
  return "todo";
}

const modelPalette = [
  "#1f4fd1",
  "#0f9d7a",
  "#d97706",
  "#c2410c",
  "#7c3aed",
  "#be185d",
  "#4b5563",
  "#0f766e",
];

function modelColor(modelKey: string) {
  let hash = 0;
  for (const char of modelKey) {
    hash = (hash * 31 + char.charCodeAt(0)) >>> 0;
  }
  return modelPalette[hash % modelPalette.length];
}

function isDailyChartMode(value: string | null | undefined): value is DailyChartMode {
  return value === "project_total";
}

function milestoneStatus(progress: ProgressSummary | null) {
  if (!progress || progress.total === null) return "Unknown";
  if (progress.blocked && progress.blocked > 0) return "Blocked";
  if (progress.percent === 100) return "Done";
  if ((progress.done ?? 0) > 0) return "Doing";
  return "Not started";
}

function modelLabel(task: Pick<TaskTokenUsageItem, "model_label">) {
  return task.model_label || "No model";
}

function fallbackText(value: string | null) {
  return value?.trim() || "Not specified";
}

function splitPrdRef(ref: string) {
  const [path, anchor] = ref.split("#", 2);
  return { path, anchor: anchor || null };
}

function isLocalMarkdownPrdRef(ref: string) {
  return splitPrdRef(ref).path.endsWith(".md");
}

function budgetState(task: TaskView | TaskTokenUsageItem) {
  if (task.token_budget === null) return "No budget";
  if (task.total_tokens === null) return "Awaiting token data";
  if (task.total_tokens > task.token_budget * 2) return "Over 2x";
  if (task.total_tokens > task.token_budget) return "Over budget";
  return "OK";
}

function taskAttention(task: TaskView | TaskTokenUsageItem) {
  const items: string[] = [];
  if (task.status === "blocked") items.push("Blocked");
  if (!task.prd_refs.length) items.push("Scope gap");
  if (task.attribution === "shared") items.push("Shared attribution");
  if (task.missing_sessions.length) items.push("Missing session link");
  if (task.status !== "done" && task.total_tokens !== null && task.token_budget !== null && task.total_tokens > task.token_budget) {
    items.push("High-token incomplete");
  }
  if (task.attribution === "unavailable") items.push("Token data unavailable");
  if (task.attribution === "none") items.push("No linked sessions");
  return items.length ? items : ["None"];
}

function hasInvalidPlan(plan: TaskPlan | null | undefined) {
  return Boolean(plan?.progress.total === null && plan?.alerts.some((alert) => alert.message.includes("invalid")));
}

function inferProjectNameFromPath(path: string) {
  const clean = path.trim().replace(/[\\/]+$/, "");
  if (!clean) return "";
  const parts = clean.split(/[\\/]/).filter(Boolean);
  return parts[parts.length - 1] ?? "";
}

export function App() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [briefing, setBriefing] = useState<BriefingResponse | null>(null);
  const [loadingProjects, setLoadingProjects] = useState(true);
  const [loadingBriefing, setLoadingBriefing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [showProjectModal, setShowProjectModal] = useState(false);
  const [draftName, setDraftName] = useState("");
  const [draftPath, setDraftPath] = useState("");
  const [hasEditedProjectName, setHasEditedProjectName] = useState(false);
  const [workspaceTab, setWorkspaceTab] = useState<WorkspaceTab>("board");
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [prdFilter, setPrdFilter] = useState<PrdFilter>("all");
  const [tokenFilter, setTokenFilter] = useState<TokenFilter>("all");

  async function loadProjects(selectFirst = true) {
    setLoadingProjects(true);
    setError(null);
    try {
      const data = await request<Project[]>("/api/projects");
      setProjects(data);
      if (data.length === 0) {
        setSelectedId(null);
      } else if (selectFirst && !selectedId && data.length > 0) {
        setSelectedId(data[0].id);
      } else if (selectedId && !data.some((project) => project.id === selectedId)) {
        setSelectedId(data[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Backend unavailable");
    } finally {
      setLoadingProjects(false);
    }
  }

  async function loadBriefing(projectId: string) {
    setLoadingBriefing(true);
    setError(null);
    try {
      setBriefing(await request<BriefingResponse>(`/api/projects/${projectId}/briefing`));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load project dashboard");
      setBriefing(null);
    } finally {
      setLoadingBriefing(false);
    }
  }

  useEffect(() => {
    void loadProjects();
  }, []);

  useEffect(() => {
    if (selectedId) {
      void loadBriefing(selectedId);
    } else {
      setBriefing(null);
    }
  }, [selectedId]);

  const selectedProject = useMemo(
    () => projects.find((project) => project.id === selectedId) ?? null,
    [projects, selectedId],
  );

  const taskViews = useMemo<TaskView[]>(() => {
    const milestones = briefing?.task_plan?.milestones ?? [];
    const usageByTaskId = new Map((briefing?.task_token_usage?.tasks ?? []).map((task) => [task.task_id, task]));
    return milestones.flatMap((milestone, milestoneIndex) =>
      milestone.tasks.map((task, taskIndex) => {
        const usage = usageByTaskId.get(task.id);
        return {
          ...task,
          milestone_id: milestone.id,
          milestone_title: milestone.title,
          milestone_index: milestoneIndex,
          task_index: taskIndex,
          total_tokens: usage?.total_tokens ?? (task.codex_sessions.length ? null : 0),
          model_label: usage?.model_label ?? (task.codex_sessions.length ? "Unknown model" : "No model"),
          models: usage?.models ?? [],
          model_providers: usage?.model_providers ?? [],
          input_tokens: usage?.input_tokens ?? null,
          cached_input_tokens: usage?.cached_input_tokens ?? null,
          output_tokens: usage?.output_tokens ?? null,
          reasoning_output_tokens: usage?.reasoning_output_tokens ?? null,
          token_budget: usage?.token_budget ?? task.token_budget,
          attribution: usage?.attribution ?? (task.codex_sessions.length ? "unavailable" : "none"),
          sessions: usage?.sessions ?? [],
          missing_sessions: usage?.missing_sessions ?? [],
          alerts: usage?.alerts ?? [],
        };
      }),
    );
  }, [briefing]);

  useEffect(() => {
    if (!taskViews.length) {
      setSelectedTaskId(null);
      return;
    }
    const firstTask = [...taskViews].sort((left, right) => (right.total_tokens ?? 0) - (left.total_tokens ?? 0))[0];
    setSelectedTaskId((current) => current ?? firstTask?.id ?? null);
  }, [taskViews]);

  const filteredTasks = useMemo(() => {
    return [...taskViews]
      .filter((task) => {
        if (statusFilter !== "all" && task.status !== statusFilter) return false;
        if (prdFilter === "linked" && task.prd_refs.length === 0) return false;
        if (prdFilter === "unlinked" && task.prd_refs.length > 0) return false;
        if (tokenFilter === "over-budget" && !(task.token_budget !== null && task.total_tokens !== null && task.total_tokens > task.token_budget)) {
          return false;
        }
        if (tokenFilter === "no-data" && task.attribution !== "none" && task.attribution !== "unavailable") return false;
        if (tokenFilter === "shared" && task.attribution !== "shared") return false;
        return true;
      })
      .sort((left, right) => (right.total_tokens ?? 0) - (left.total_tokens ?? 0));
  }, [prdFilter, statusFilter, taskViews, tokenFilter]);

  const milestoneSummaries = useMemo(
    () =>
      (briefing?.task_plan?.milestones ?? []).map((milestone) => {
        const milestoneTasks = taskViews.filter((task) => task.milestone_id === milestone.id);
        const linked = milestoneTasks.filter((task) => task.prd_refs.length > 0).length;
        const tokens = milestoneTasks.reduce((sum, task) => sum + (task.total_tokens ?? 0), 0);
        return {
          id: milestone.id,
          title: milestone.title,
          progress: milestone.progress,
          done: milestoneTasks.filter((task) => task.status === "done").length,
          total: milestoneTasks.length,
          blocked: milestoneTasks.filter((task) => task.status === "blocked").length,
          linked,
          tokens,
        };
      }),
    [briefing?.task_plan?.milestones, taskViews],
  );

  const coverageRows = useMemo<CoverageRow[]>(() => {
    const groups = new Map<string, TaskView[]>();
    for (const task of taskViews) {
      const refs = task.prd_refs.length ? task.prd_refs : ["Unlinked PRD"];
      for (const ref of refs) {
        groups.set(ref, [...(groups.get(ref) ?? []), task]);
      }
    }
    return [...groups.entries()]
      .map(([ref, tasks]) => {
        const required = tasks.length;
        const covered = tasks.filter((task) => task.status === "done").length;
        const coverage = required === 0 ? 0 : Math.round((covered / required) * 100);
        return {
          ref,
          required,
          covered,
          coverage,
          tokens: tasks.reduce((sum, task) => sum + (task.total_tokens ?? 0), 0),
          attention: tasks.some((task) => taskAttention(task)[0] !== "None") ? "Review needed" : "Clear",
        };
      })
      .sort((left, right) => right.coverage - left.coverage);
  }, [taskViews]);

  const linkedTasks = taskViews.filter((task) => task.prd_refs.length > 0).length;
  const overBudgetCount = taskViews.filter(
    (task) => task.token_budget !== null && task.total_tokens !== null && task.total_tokens > task.token_budget,
  ).length;
  const modelsInUse = new Set(taskViews.flatMap((task) => task.models).filter(Boolean)).size;
  const sharedCount = taskViews.filter((task) => task.attribution === "shared").length;
  const linkedSessionCount = new Set(taskViews.flatMap((task) => task.codex_sessions)).size;
  const totalTasks = taskViews.length;
  const progress = briefing?.task_plan?.progress ?? briefing?.progress ?? { done: null, total: null, blocked: null, percent: null };
  const coveragePercent = totalTasks === 0 ? 0 : Math.round((linkedTasks / totalTasks) * 100);

  const topAttention = useMemo(() => {
    if (!taskViews.length) return 0;
    return taskViews.filter((task) => taskAttention(task)[0] !== "None").length;
  }, [taskViews]);

  function openProjectModal() {
    setFormError(null);
    setDraftName("");
    setDraftPath("");
    setHasEditedProjectName(false);
    setShowProjectModal(true);
  }

  function closeProjectModal() {
    setShowProjectModal(false);
    setFormError(null);
  }

  function handleProjectPathChange(value: string) {
    setDraftPath(value);
    if (!hasEditedProjectName || !draftName.trim()) {
      setDraftName(inferProjectNameFromPath(value));
    }
  }

  async function submitProject(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    try {
      const project = await request<Project>("/api/projects", {
        method: "POST",
        body: JSON.stringify({ name: draftName, path: draftPath }),
      });
      closeProjectModal();
      await loadProjects(false);
      setSelectedId(project.id);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Could not add project");
    }
  }

  async function removeProject(projectId: string) {
    try {
      await request(`/api/projects/${projectId}`, { method: "DELETE" });
      if (selectedId === projectId) {
        setBriefing(null);
      }
      await loadProjects(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not remove project");
    }
  }

  return (
    <main className="pm-shell">
      <aside className="pm-rail">
        <div className="rail-brand">
          <div className="rail-logo">A</div>
          <span>AgentPM</span>
        </div>

        <nav className="rail-nav">
          {mainNav.map((item) => {
            const Icon = item.icon;
            return (
              <button key={item.id} type="button" className={item.active ? "rail-link active" : "rail-link"}>
                <Icon size={16} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        <section className="project-sidebar">
          <div className="sidebar-section-title">
            <span>Projects</span>
            <div className="sidebar-section-actions">
              <button type="button" className="ghost-icon" onClick={openProjectModal} aria-label="Add project">
                <Plus size={14} />
              </button>
              <button type="button" className="ghost-icon" onClick={() => void loadProjects(false)} aria-label="Refresh projects">
                <RefreshCw size={14} />
              </button>
            </div>
          </div>

          <ProjectList
            loading={loadingProjects}
            projects={projects}
            selectedId={selectedId}
            onSelect={setSelectedId}
            onRemove={removeProject}
            activeStatus={briefing?.briefing.status ?? "unknown"}
          />
        </section>

        <div className="sidebar-user">
          <div className="user-avatar">JP</div>
          <div>
            <strong>John Parker</strong>
            <span>PM</span>
          </div>
          <ChevronDown size={14} />
        </div>
      </aside>

      <section className="pm-main">
        {error ? <Banner level="error" message={error} /> : null}
        {loadingBriefing ? <LoadingState label="Loading PM board" /> : null}
        {!loadingBriefing && !selectedProject && !error ? <EmptyState /> : null}
        {!loadingBriefing && selectedProject && briefing ? (
          <ProjectBoard
            briefing={briefing}
            onRefresh={() => void loadBriefing(briefing.project.id)}
            workspaceTab={workspaceTab}
            onTabChange={setWorkspaceTab}
            selectedTaskId={selectedTaskId}
            onSelectTask={setSelectedTaskId}
            filteredTasks={filteredTasks}
            milestoneSummaries={milestoneSummaries}
            progress={progress}
            topAttention={topAttention}
            linkedSessionCount={linkedSessionCount}
            overBudgetCount={overBudgetCount}
            modelsInUse={modelsInUse}
            coveragePercent={coveragePercent}
            sharedCount={sharedCount}
            totalTasks={totalTasks}
            statusFilter={statusFilter}
            setStatusFilter={setStatusFilter}
            prdFilter={prdFilter}
            setPrdFilter={setPrdFilter}
            tokenFilter={tokenFilter}
            setTokenFilter={setTokenFilter}
          />
        ) : null}
      </section>

      {showProjectModal ? (
        <ProjectModal
          name={draftName}
          path={draftPath}
          formError={formError}
          onClose={closeProjectModal}
          onSubmit={submitProject}
          onNameChange={(value) => {
            setHasEditedProjectName(true);
            setDraftName(value);
          }}
          onPathChange={handleProjectPathChange}
        />
      ) : null}
    </main>
  );
}

function ProjectList({
  loading,
  projects,
  selectedId,
  onSelect,
  onRemove,
  activeStatus,
}: {
  loading: boolean;
  projects: Project[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onRemove: (id: string) => void;
  activeStatus: BriefingStatus;
}) {
  if (loading) return <LoadingState label="Loading projects" compact />;
  if (projects.length === 0) return <EmptyPanel label="No projects registered yet." compact />;
  return (
    <div className="project-collection">
      {projects.map((project, index) => {
        const selected = project.id === selectedId;
        const status = selected ? projectHealthFromBriefing(activeStatus) : index % 3 === 0 ? "Active" : index % 3 === 1 ? "On Track" : "At Risk";
        return (
          <div key={project.id} className={selected ? "project-card active" : "project-card"}>
            <button type="button" className="project-card-main" onClick={() => onSelect(project.id)}>
              <div className="project-card-avatar">{project.name[0] ?? "P"}</div>
              <div className="project-card-copy">
                <strong>{project.name}</strong>
                <span className={`health-label ${statusToneFromHealth(status)}`}>{status}</span>
              </div>
            </button>
            <button
              type="button"
              className="card-remove-button"
              aria-label={`Remove ${project.name}`}
              title={`Remove ${project.name}`}
              onClick={(event) => {
                event.stopPropagation();
                if (window.confirm(`Remove project "${project.name}" from the list?`)) {
                  void onRemove(project.id);
                }
              }}
            >
              <Trash2 size={14} />
            </button>
          </div>
        );
      })}
    </div>
  );
}

function ProjectBoard(props: {
  briefing: BriefingResponse;
  onRefresh: () => void;
  workspaceTab: WorkspaceTab;
  onTabChange: (tab: WorkspaceTab) => void;
  selectedTaskId: string | null;
  onSelectTask: (taskId: string) => void;
  filteredTasks: TaskView[];
  milestoneSummaries: {
    id: string;
    title: string;
    progress: ProgressSummary | null;
    done: number;
    total: number;
    blocked: number;
    linked: number;
    tokens: number;
  }[];
  progress: ProgressSummary;
  topAttention: number;
  linkedSessionCount: number;
  overBudgetCount: number;
  modelsInUse: number;
  coveragePercent: number;
  sharedCount: number;
  totalTasks: number;
  statusFilter: StatusFilter;
  setStatusFilter: (value: StatusFilter) => void;
  prdFilter: PrdFilter;
  setPrdFilter: (value: PrdFilter) => void;
  tokenFilter: TokenFilter;
  setTokenFilter: (value: TokenFilter) => void;
}) {
  const {
    briefing,
    onRefresh,
    workspaceTab,
    onTabChange,
    selectedTaskId,
    onSelectTask,
    filteredTasks,
    milestoneSummaries,
    progress,
    topAttention,
    linkedSessionCount,
    overBudgetCount,
    modelsInUse,
    coveragePercent,
    sharedCount,
    totalTasks,
    statusFilter,
    setStatusFilter,
    prdFilter,
    setPrdFilter,
    tokenFilter,
    setTokenFilter,
  } = props;

  const [dailyChartMode, setDailyChartMode] = useState<DailyChartMode>("project_total");
  const [prdModal, setPrdModal] = useState<{
    ref: string;
    document: PrdDocumentResponse | null;
    loading: boolean;
    error: string | null;
  } | null>(null);
  const StatusIcon = statusIcon[briefing.briefing.status];
  const topTokenTasks = filteredTasks.slice(0, 7);
  const dailyUsage = briefing.daily_token_usage;
  const backendDailyChartMode = isDailyChartMode(dailyUsage?.default_mode) ? dailyUsage.default_mode : "project_total";
  const dailyChartModel = buildDailyChartModel(dailyUsage, dailyChartMode);
  const attentionAlerts = briefing.alerts
    .filter((alert, index, list) => list.findIndex((item) => item.message === alert.message) === index)
    .slice(0, 4);

  useEffect(() => {
    setDailyChartMode(backendDailyChartMode);
  }, [backendDailyChartMode, briefing.project.id]);

  useEffect(() => {
    setPrdModal(null);
  }, [briefing.project.id]);

  async function openPrd(ref: string) {
    setPrdModal({ ref, document: null, loading: true, error: null });
    try {
      const document = await request<PrdDocumentResponse>(`/api/projects/${briefing.project.id}/prd?ref=${encodeURIComponent(ref)}`);
      setPrdModal({ ref, document, loading: false, error: null });
    } catch (err) {
      setPrdModal({ ref, document: null, loading: false, error: err instanceof Error ? err.message : "Could not load PRD" });
    }
  }

  return (
    <div className="board-frame">
      <header className="board-topbar">
        <div className="board-title-group">
          <div className="board-title-mark">A</div>
          <div>
            <div className="board-title-line">
              <h1>{briefing.project.name}</h1>
              <ChevronDown size={14} />
            </div>
            <p>{briefing.project.path}</p>
          </div>
        </div>

        <div className="board-toolbar">
          <button type="button" className="toolbar-button">
            <CalendarRange size={15} />
            <span>Current project view</span>
          </button>
          <button type="button" className="toolbar-button">
            <Filter size={15} />
            <span>Filters</span>
          </button>
          <button type="button" className="toolbar-icon" onClick={onRefresh}>
            <RefreshCw size={15} />
          </button>
        </div>
      </header>

      <div className="workspace-tabs">
        {workspaceTabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={workspaceTab === tab.id ? "workspace-tab active" : "workspace-tab"}
            onClick={() => onTabChange(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="board-content">
        <section className="board-center">
          <section className="kpi-grid kpi-grid-three">
            <KpiCard
              title="Delivery health"
              value={progress.percent === null ? "Plan unavailable" : `${progress.percent}%`}
              subline={`${progress.done ?? 0} / ${progress.total ?? 0} tasks complete · ${progress.blocked ?? 0} blocked`}
              accent={progress.percent ?? 0}
              accentTone="green"
            />
            <KpiCard
              title="Scope coverage"
              value={`${coveragePercent}%`}
              subline={`${Math.round((coveragePercent / 100) * totalTasks)} / ${totalTasks} tasks linked to PRD`}
              accent={coveragePercent}
              accentTone="blue"
            />
            <KpiCard
              title="Cost + attention"
              value={briefing.tokens.unavailable ? "Unavailable" : compactTokens(briefing.tokens.total)}
              subline={`${modelsInUse || 1} models in use · ${linkedSessionCount} linked sessions`}
              trend={overBudgetCount ? `${overBudgetCount} tasks over budget` : `${topAttention} tasks need PM review`}
              highlight={sharedCount ? `${sharedCount} tasks use shared attribution` : "No shared attribution issues"}
              accentTone="red"
            />
          </section>

          {workspaceTab === "board" ? (
            <>
              <section className="board-row board-row-analytics">
                <section className="panel daily-token-panel">
                  <div className="panel-header panel-header-spread">
                    <div>
                      <span className="panel-eyebrow">Board insight</span>
                      <h3>Daily token usage</h3>
                    </div>
                    <div className="segmented-control" role="tablist" aria-label="Daily token usage modes">
                      <button type="button" className="segment-button active">
                        Project total
                      </button>
                    </div>
                  </div>

                  <DailyTokenUsageChart model={dailyChartModel} />

                  {dailyChartModel.supportingText ? <p className="panel-note">{dailyChartModel.supportingText}</p> : null}
                </section>

                <section className="panel attention-panel">
                  <PanelHeader title="Attention queue" />
                  <div className="attention-list">
                    {attentionAlerts.length ? (
                      attentionAlerts.map((alert) => (
                        <div key={`${alert.level}-${alert.message}`} className={`attention-item ${alert.level}`}>
                          <strong>{alert.message}</strong>
                          <span>{alert.level === "info" ? "Visibility signal" : "Needs review"}</span>
                        </div>
                      ))
                    ) : (
                      <EmptyPanel label="No immediate PM attention items." compact />
                    )}
                  </div>
                </section>
              </section>

              <section className="board-row board-row-top">
                <section className="panel roadmap-panel">
                  <PanelHeader title="Milestone roadmap" />
                  <MilestoneRoadmap milestones={milestoneSummaries} onSelectTask={onSelectTask} />
                </section>
              </section>

              <section className="board-row board-row-bottom">
                <section className="panel tasks-panel tasks-panel-full">
                  <PanelHeader title={`Tasks (${totalTasks})`} />
                  <TableFilters
                    statusFilter={statusFilter}
                    setStatusFilter={setStatusFilter}
                    prdFilter={prdFilter}
                    setPrdFilter={setPrdFilter}
                    tokenFilter={tokenFilter}
                    setTokenFilter={setTokenFilter}
                  />
                  <TasksTable tasks={filteredTasks} selectedTaskId={selectedTaskId} onSelectTask={onSelectTask} onOpenPrd={openPrd} />
                </section>
              </section>
            </>
          ) : (
            <section className="panel">
              <PanelHeader title={workspaceTabs.find((tab) => tab.id === workspaceTab)?.label ?? "Section"} />
              {workspaceTab === "prd" ? (
                <TasksTable
                  tasks={filteredTasks.filter((task) => task.prd_refs.length > 0)}
                  selectedTaskId={selectedTaskId}
                  onSelectTask={onSelectTask}
                  onOpenPrd={openPrd}
                />
              ) : workspaceTab === "tasks" ? (
                <>
                  <TableFilters
                    statusFilter={statusFilter}
                    setStatusFilter={setStatusFilter}
                    prdFilter={prdFilter}
                    setPrdFilter={setPrdFilter}
                    tokenFilter={tokenFilter}
                    setTokenFilter={setTokenFilter}
                  />
                  <TasksTable tasks={filteredTasks} selectedTaskId={selectedTaskId} onSelectTask={onSelectTask} onOpenPrd={openPrd} />
                </>
              ) : workspaceTab === "milestones" ? (
                <MilestoneRoadmap milestones={milestoneSummaries} onSelectTask={onSelectTask} />
              ) : workspaceTab === "sessions" ? (
                <TokenUsageList tasks={topTokenTasks} selectedTaskId={selectedTaskId} onSelectTask={onSelectTask} />
              ) : (
                <EmptyPanel label="This section is reserved for the next PM workflow slice." />
              )}
            </section>
          )}
        </section>
      </div>

      {prdModal ? <PrdModal state={prdModal} onClose={() => setPrdModal(null)} /> : null}
    </div>
  );
}

function KpiCard({
  title,
  value,
  subline,
  accent,
  accentTone,
  trend,
  highlight,
}: {
  title: string;
  value: string;
  subline: string;
  accent?: number;
  accentTone: "green" | "blue" | "plain" | "red";
  trend?: string;
  highlight?: string;
}) {
  return (
    <article className="kpi-card">
      <div className="kpi-label-row">
        <span>{title}</span>
        <AlertTriangle size={13} />
      </div>
      <strong>{value}</strong>
      {typeof accent === "number" ? (
        <div className="kpi-progress">
          <div className={`kpi-progress-fill ${accentTone}`} style={{ width: `${Math.min(accent, 100)}%` }} />
        </div>
      ) : null}
      <p>{subline}</p>
      {trend ? <small className="trend positive">{trend}</small> : null}
      {highlight ? <small className={accentTone === "red" ? "trend negative" : "trend"}>{highlight}</small> : null}
    </article>
  );
}

function DailyTokenUsageChart({
  model,
}: {
  model: ReturnType<typeof buildDailyChartModel>;
}) {
  if (!model.series.length) {
    return (
      <div className="inline-state">
        <p>{model.supportingText || "Daily token usage unavailable."}</p>
      </div>
    );
  }

  const allBars = model.series.flatMap((series) => series.bars);
  const dates = [...new Set(allBars.map((bar) => bar.date))].sort((left, right) => left.localeCompare(right));
  const maxValue = Math.max(...allBars.map((bar) => bar.value), 1);
  const chartHeight = 220;
  const plotHeight = 160;
  const chartWidth = Math.max(dates.length * 76, 320);
  const leftPad = 18;
  const rightPad = 18;
  const topPad = 16;
  const bottomPad = 40;
  const innerWidth = chartWidth - leftPad - rightPad;
  const bandWidth = innerWidth / Math.max(dates.length, 1);
  const barWidth = Math.min(34, bandWidth * 0.56);
  const axisY = topPad + plotHeight;
  const gridValues = [0, 0.25, 0.5, 0.75, 1];
  const showValueLabels = dates.length <= 8;

  return (
    <div className="daily-chart-card">
      <svg
        className="daily-chart-svg"
        viewBox={`0 0 ${chartWidth} ${chartHeight}`}
        role="img"
        aria-label="Daily token usage column chart"
      >
        {gridValues.map((ratio) => {
          const y = topPad + plotHeight - plotHeight * ratio;
          return (
            <g key={ratio}>
              <line x1={leftPad} y1={y} x2={chartWidth - rightPad} y2={y} className="daily-chart-grid" />
              <text x={leftPad - 6} y={y + 4} textAnchor="end" className="daily-chart-axis-label">
                {ratio === 0 ? "0" : compactTokens(Math.round(maxValue * ratio))}
              </text>
            </g>
          );
        })}
        <line x1={leftPad} y1={axisY} x2={chartWidth - rightPad} y2={axisY} className="daily-chart-axis" />

        {dates.map((date, index) => {
          const x = leftPad + index * bandWidth + (bandWidth - barWidth) / 2;
          const series = model.series[0];
          const bar = series?.bars.find((item) => item.date === date);
          const value = bar?.value ?? 0;
          let stackedHeight = 0;
          return (
            <g key={date}>
              {(bar?.segments ?? []).map((segment, segmentIndex, segments) => {
                if (!segment.value) return null;
                const height = Math.max((segment.value / maxValue) * plotHeight, 4);
                const y = axisY - stackedHeight - height;
                stackedHeight += height;
                const isTopSegment = segmentIndex === segments.length - 1;
                return (
                  <rect
                    key={`${date}-${segment.id}`}
                    x={x}
                    y={y}
                    width={barWidth}
                    height={height}
                    rx={isTopSegment ? 8 : 0}
                    fill={modelColor(segment.id)}
                    className="daily-chart-rect"
                  >
                    <title>{`${segment.label}: ${compactTokens(segment.value)}`}</title>
                  </rect>
                );
              })}
              <text x={x + barWidth / 2} y={axisY + 14} textAnchor="middle" className="daily-chart-date-label">
                {formatShortDay(date)}
              </text>
              {showValueLabels ? (
                <text x={x + barWidth / 2} y={axisY - stackedHeight - 6} textAnchor="middle" className="daily-chart-value-label">
                  {compactTokens(value)}
                </text>
              ) : null}
            </g>
          );
        })}
      </svg>

      {model.legend.length ? (
        <div className="daily-chart-legend">
          {model.legend.map((item) => (
            <span key={item.id} className="detail-chip legend-chip">
              <span className="legend-swatch" style={{ backgroundColor: modelColor(item.id) }} aria-hidden="true" />
              {item.label}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function PanelHeader({ title }: { title: string }) {
  return (
    <div className="panel-header">
      <h3>{title}</h3>
      <AlertTriangle size={13} />
    </div>
  );
}

function MilestoneRoadmap({
  milestones,
  onSelectTask,
}: {
  milestones: {
    id: string;
    title: string;
    progress: ProgressSummary | null;
    done: number;
    total: number;
    blocked: number;
    linked: number;
    tokens: number;
  }[];
  onSelectTask: (taskId: string) => void;
}) {
  if (!milestones.length) return <EmptyPanel label="Add agentpm.yaml to show roadmap progress." />;
  return (
    <div className="roadmap-table">
      <div className="roadmap-head">
        <span>Milestone</span>
        <span>Progress</span>
        <span>Status</span>
      </div>
      {milestones.map((milestone, index) => {
        const status = milestoneStatus(milestone.progress);
        return (
          <div key={milestone.id} className="roadmap-row">
            <div className="roadmap-label">
              <strong>{index + 1}. {milestone.title}</strong>
              <small>{milestone.done} / {milestone.total} complete · {compactTokens(milestone.tokens)}</small>
            </div>
            <div className="roadmap-progress">
              <span>{milestone.progress?.percent ?? 0}%</span>
              <div className="roadmap-progress-bar">
                <div style={{ width: `${milestone.progress?.percent ?? 0}%` }} />
              </div>
            </div>
            <div className={`roadmap-status ${statusToneFromHealth(status)}`}>
              {status === "Done" ? <Check size={13} /> : status === "Doing" ? <Clock3 size={13} /> : status === "Blocked" ? <AlertTriangle size={13} /> : <CircleSlash size={13} />}
              <span>{status}</span>
            </div>
          </div>
        );
      })}
      <button type="button" className="inline-link" onClick={() => onSelectTask(milestones[0]?.id ?? "")}>
        View full roadmap
        <ChevronRight size={14} />
      </button>
    </div>
  );
}

function TokenUsageList({
  tasks,
  selectedTaskId,
  onSelectTask,
}: {
  tasks: TaskView[];
  selectedTaskId: string | null;
  onSelectTask: (taskId: string) => void;
}) {
  if (!tasks.length) return <EmptyPanel label="No task token data available yet." />;
  const maxTokens = Math.max(...tasks.map((task) => task.total_tokens ?? 0), 1);
  return (
    <div className="token-list">
      {tasks.map((task) => (
        <button
          key={task.id}
          type="button"
          className={task.id === selectedTaskId ? "token-row active" : "token-row"}
          onClick={() => onSelectTask(task.id)}
        >
          <div className="token-row-copy">
            <strong>{task.title}</strong>
            <small>{shortenModelList(task)}</small>
          </div>
          <div className="token-row-bar">
            <div className={`token-row-fill ${statusTone(task.status)}`} style={{ width: `${((task.total_tokens ?? 0) / maxTokens) * 100}%` }} />
          </div>
          <span>{compactTokens(task.total_tokens)}</span>
        </button>
      ))}
      <button type="button" className="inline-link">
        View all tasks
        <ChevronRight size={14} />
      </button>
    </div>
  );
}

function TableFilters({
  statusFilter,
  setStatusFilter,
  prdFilter,
  setPrdFilter,
  tokenFilter,
  setTokenFilter,
}: {
  statusFilter: StatusFilter;
  setStatusFilter: (value: StatusFilter) => void;
  prdFilter: PrdFilter;
  setPrdFilter: (value: PrdFilter) => void;
  tokenFilter: TokenFilter;
  setTokenFilter: (value: TokenFilter) => void;
}) {
  return (
    <div className="table-filters">
      <FilterSelect
        label="Status"
        value={statusFilter}
        onChange={setStatusFilter}
        options={[
          { value: "all", label: "All" },
          { value: "todo", label: "Todo" },
          { value: "doing", label: "Doing" },
          { value: "blocked", label: "Blocked" },
          { value: "done", label: "Done" },
        ]}
      />
      <FilterSelect
        label="PRD"
        value={prdFilter}
        onChange={setPrdFilter}
        options={[
          { value: "all", label: "All" },
          { value: "linked", label: "Linked" },
          { value: "unlinked", label: "Unlinked" },
        ]}
      />
      <FilterSelect
        label="Tokens"
        value={tokenFilter}
        onChange={setTokenFilter}
        options={[
          { value: "all", label: "All" },
          { value: "over-budget", label: "Over budget" },
          { value: "no-data", label: "No data" },
          { value: "shared", label: "Shared" },
        ]}
      />
    </div>
  );
}

function FilterSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: any) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <label className="filter-field">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function TasksTable({
  tasks,
  selectedTaskId,
  onSelectTask,
  onOpenPrd,
}: {
  tasks: TaskView[];
  selectedTaskId: string | null;
  onSelectTask: (taskId: string) => void;
  onOpenPrd: (ref: string) => void;
}) {
  if (!tasks.length) return <EmptyPanel label="No tasks match the current filters." />;
  return (
    <div className="tasks-table">
      <div className="tasks-head">
        <span>Task</span>
        <span>PRD</span>
        <span>User story</span>
        <span>Scope</span>
        <span>Acceptance</span>
        <span>Verification</span>
        <span>Status</span>
        <span>Tokens</span>
        <span>Budget</span>
        <span>Attention</span>
      </div>
      {tasks.map((task) => (
        <div key={task.id} className={task.id === selectedTaskId ? "tasks-row active" : "tasks-row"} onClick={() => onSelectTask(task.id)}>
          <div className="tasks-main-cell">
            <strong>{task.title}</strong>
            <small>{task.id}</small>
            <small className="task-model-line">{shortenModelList(task)}</small>
          </div>
          <div className="prd-ref-list">
            {task.prd_refs.length ? (
              task.prd_refs.map((ref) =>
                isLocalMarkdownPrdRef(ref) ? (
                  <button
                    key={ref}
                    type="button"
                    className="prd-link-chip"
                    onClick={(event) => {
                      event.stopPropagation();
                      onOpenPrd(ref);
                    }}
                  >
                    {ref}
                  </button>
                ) : (
                  <span key={ref} className="detail-chip">
                    {ref}
                  </span>
                ),
              )
            ) : (
              <span className="pill danger">Unlinked PRD</span>
            )}
          </div>
          <span className="task-detail-text">{fallbackText(task.user_story)}</span>
          <span className="task-detail-text">{fallbackText(task.scope)}</span>
          <span className="task-detail-text">{fallbackText(task.acceptance_criteria)}</span>
          <span className="task-detail-text">{fallbackText(task.verification_method)}</span>
          <span className={`pill status ${statusTone(task.status)}`}>{task.status}</span>
          <span>{compactTokens(task.total_tokens)}</span>
          <span className={budgetState(task).startsWith("Over") ? "budget-alert" : ""}>{budgetState(task)}</span>
          <span>{taskAttention(task)[0]}</span>
        </div>
      ))}
    </div>
  );
}

function PrdModal({
  state,
  onClose,
}: {
  state: { ref: string; document: PrdDocumentResponse | null; loading: boolean; error: string | null };
  onClose: () => void;
}) {
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  const title = state.document?.title ?? state.ref;
  const subtitle = state.document
    ? [state.document.path, state.document.anchor ? `#${state.document.anchor}` : ""].filter(Boolean).join("")
    : state.ref;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <section className="project-modal prd-modal" onClick={(event) => event.stopPropagation()} aria-modal="true" role="dialog">
        <div className="project-modal-header">
          <div>
            <p className="eyebrow">PRD reference</p>
            <h2>{title}</h2>
            <span className="prd-modal-path">{subtitle}</span>
          </div>
          <button type="button" className="ghost-icon" onClick={onClose} aria-label="Close PRD">
            <X size={16} />
          </button>
        </div>

        {state.loading ? (
          <LoadingState label="Loading PRD" compact />
        ) : state.error ? (
          <Banner level="error" message={state.error} />
        ) : state.document?.unavailable ? (
          <EmptyPanel label="PRD content is unavailable for this reference." />
        ) : (
          <pre className="prd-content">{state.document?.content}</pre>
        )}
      </section>
    </div>
  );
}

function Banner({ level, message }: { level: AlertLevel; message: string }) {
  return (
    <div className={`banner ${level}`}>
      <AlertTriangle size={16} />
      <span>{message}</span>
    </div>
  );
}

function LoadingState({ label, compact = false }: { label: string; compact?: boolean }) {
  return (
    <div className={compact ? "loading compact" : "loading"}>
      <Loader2 size={18} />
      <span>{label}</span>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="empty-state">
      <Wallet size={28} />
      <h2>Select or add a project</h2>
      <p>Register a local project path to see PM board analytics, task progress, and token usage.</p>
    </div>
  );
}

function EmptyPanel({ label, compact = false }: { label: string; compact?: boolean }) {
  return (
    <div className={compact ? "empty-panel compact" : "empty-panel"}>
      <AlertTriangle size={16} />
      <span>{label}</span>
    </div>
  );
}

function ProjectModal({
  name,
  path,
  formError,
  onClose,
  onSubmit,
  onNameChange,
  onPathChange,
}: {
  name: string;
  path: string;
  formError: string | null;
  onClose: () => void;
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
  onNameChange: (value: string) => void;
  onPathChange: (value: string) => void;
}) {
  const [browserState, setBrowserState] = useState<DirectoryBrowseResponse | null>(null);
  const [loadingBrowser, setLoadingBrowser] = useState(false);
  const [browserError, setBrowserError] = useState<string | null>(null);

  async function loadDirectories(targetPath?: string) {
    setLoadingBrowser(true);
    setBrowserError(null);
    try {
      const query = targetPath ? `?path=${encodeURIComponent(targetPath)}` : "";
      setBrowserState(await request<DirectoryBrowseResponse>(`/api/directories${query}`));
    } catch (err) {
      setBrowserError(err instanceof Error ? err.message : "Could not load folders");
    } finally {
      setLoadingBrowser(false);
    }
  }

  useEffect(() => {
    void loadDirectories();
  }, []);

  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <div className="project-modal" role="dialog" aria-modal="true" aria-labelledby="project-modal-title" onClick={(event) => event.stopPropagation()}>
        <div className="project-modal-header">
          <div>
            <p className="eyebrow">Project setup</p>
            <h2 id="project-modal-title">Add local project</h2>
          </div>
          <button type="button" className="ghost-icon" onClick={onClose} aria-label="Close">
            <X size={15} />
          </button>
        </div>

        <form className="project-modal-form" onSubmit={onSubmit}>
          <section className="folder-browser">
            <div className="folder-browser-header">
              <div className="folder-browser-copy">
                <span className="eyebrow">Folder browser</span>
                <strong>{browserState?.current_path ?? "Available folders"}</strong>
              </div>
              <div className="folder-browser-actions">
                {browserState?.parent_path ? (
                  <button type="button" className="toolbar-button" onClick={() => void loadDirectories(browserState.parent_path ?? undefined)}>
                    <StepBack size={14} />
                    Up
                  </button>
                ) : null}
                <button
                  type="button"
                  className="primary-action"
                  onClick={() => {
                    if (browserState?.current_path) onPathChange(browserState.current_path);
                  }}
                >
                  Use this folder
                </button>
              </div>
            </div>

            {browserState?.roots.length ? (
              <div className="root-chip-wrap">
                {browserState.roots.map((root) => (
                  <button key={root.path} type="button" className="detail-chip browse-root-chip" onClick={() => void loadDirectories(root.path)}>
                    {root.label}
                  </button>
                ))}
              </div>
            ) : null}

            {loadingBrowser ? <LoadingState label="Loading folders" compact /> : null}
            {browserError ? <p className="inline-error">{browserError}</p> : null}

            <div className="folder-list">
              {browserState?.directories.map((directory) => (
                <button key={directory.path} type="button" className="folder-row" onClick={() => void loadDirectories(directory.path)}>
                  <span>{directory.name}</span>
                  <ChevronRight size={14} />
                </button>
              ))}
              {!loadingBrowser && browserState && browserState.directories.length === 0 ? <EmptyPanel label="No subfolders here." compact /> : null}
            </div>
          </section>

          <label className="modal-field">
            <span>Project path</span>
            <input value={path} onChange={(event) => onPathChange(event.target.value)} placeholder="/Users/ray/BaiduNetDisk/Project/Example" />
          </label>

          <label className="modal-field">
            <span>Project name</span>
            <input value={name} onChange={(event) => onNameChange(event.target.value)} placeholder="Example" />
          </label>

          {formError ? <p className="inline-error">{formError}</p> : null}

          <div className="project-modal-actions">
            <button type="button" className="toolbar-button" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="primary-action">
              <Plus size={14} />
              Add project
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function projectHealthFromBriefing(status: BriefingStatus) {
  if (status === "blocked") return "At Risk";
  if (status === "tests_failing") return "At Risk";
  if (status === "active") return "Active";
  if (status === "idle") return "On Track";
  return "Needs Review";
}

function statusToneFromHealth(value: string) {
  if (value === "Done" || value === "Active" || value === "On Track") return "done";
  if (value === "Doing") return "doing";
  if (value === "Blocked" || value === "At Risk") return "blocked";
  return "todo";
}
