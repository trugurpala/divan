import { useEffect, useMemo, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { open } from "@tauri-apps/plugin-dialog";
import DoctorPanel, { type Depth, type DoctorPayload } from "./DoctorPanel";
import FirstRunWizard, { capabilityLine, pendingLine } from "./FirstRunWizard";
import PatronDesk, { PatronDeskPanel } from "./PatronDesk";
import {
  PluginInspectorRail,
  PluginTrustCenter,
  type PluginInspection,
} from "./PluginTrustCenter";
import ProjectStatusCard from "./ProjectStatusCard";
import { type AgencyStatus, patronSummary } from "./humanStatus";

type CoreEnvelope<T> = {
  api_version: number;
  ok: boolean;
  result?: T;
  error?: { code: string; message: string };
};

type Capabilities = {
  product: string;
  api_version?: number;
  apiVersion?: number;
  engines?: string[];
  features: string[];
  commands?: string[];
};

type ShellCapabilities = {
  product: string;
  version: string;
  apiVersion: number;
  shell: string;
  features: string[];
};

type UpdateStatus = {
  available: boolean;
  version: string | null;
};

type UpdateInstallStatus = {
  installed: boolean;
  version: string | null;
};

type ToolStatus = {
  id: string;
  display_name: string;
  available: boolean;
  path: string | null;
  required: boolean;
  version: string | null;
  auth: string;
  auth_detail: string | null;
  subscription_supported: boolean;
  api_key_configured: boolean;
  app_installed: boolean;
  app_version: string | null;
};

type Readiness = {
  ready: boolean;
  tools: ToolStatus[];
  engines: string[];
  recommended_engine: string | null;
  recommended_agent: string | null;
  api_keys_required: boolean;
};

type ProjectRecord = {
  project_id: string;
  name: string;
  root: string;
  created_at: string;
  last_opened_at: string;
};

type CoreTask = {
  task_id: string;
  title: string;
  state: string;
  project_root: string | null;
  engine_id: string | null;
  mandate_id: string | null;
  metadata: Record<string, unknown>;
  events: unknown[];
};

type EvidenceRecord = {
  task_id: string;
  kind: string;
  status: string;
  summary: string;
  at: string;
  data: Record<string, unknown>;
  sha256: string;
};

type TaskDiff = {
  engine: string;
  ok: boolean;
  exit_code: number;
  path: string;
  diff: string;
};

type ReviewResult = {
  task: CoreTask;
  review: {
    verdict: string;
    checks: Array<Record<string, unknown>>;
    reasons: string[];
  };
};

type UiState = "PLAN" | "WORKING" | "REVIEW" | "PASS" | "APPROVAL";
type ActiveTab =
  | "taht"
  | "summary"
  | "evidence"
  | "diff"
  | "releases"
  | "settings"
  | "plugins"
  | "archive"
  | "system";

/**
 * The seven Patron destinations, in the order the sidebar shows them. A tab
 * that has no destination of its own (diff, releases) lights up its group.
 */
type NavItem = { label: string; tab: ActiveTab; group: readonly ActiveTab[] };
const NAV_ITEMS: readonly NavItem[] = [
  { label: "👑 TAHT", tab: "taht", group: ["taht"] },
  { label: "🏛 DİVAN", tab: "summary", group: ["summary", "diff"] },
  { label: "⚔ EKİP", tab: "settings", group: ["settings"] },
  { label: "🕵 TEFTİŞ", tab: "evidence", group: ["evidence"] },
  { label: "🧠 ARŞİV", tab: "archive", group: ["archive"] },
  { label: "🧰 CEPHANELİK", tab: "plugins", group: ["plugins"] },
  { label: "🩺 SİSTEM", tab: "system", group: ["system", "releases"] },
];

const DEPTH_OPTIONS: ReadonlyArray<[Depth, string]> = [
  ["padisah", "Patron"],
  ["divan", "Divan"],
  ["teknik", "Teknik"],
];

const FIRST_RUN_KEY = "divan.firstRunDone";

function readFirstRunDone(): boolean {
  try {
    return window.localStorage.getItem(FIRST_RUN_KEY) === "1";
  } catch {
    return false;
  }
}

function writeFirstRunDone(): void {
  try {
    window.localStorage.setItem(FIRST_RUN_KEY, "1");
  } catch {
    // Storage may be unavailable; the wizard simply shows again next start.
  }
}

const stateMap: Record<string, UiState> = {
  draft: "PLAN",
  planned: "PLAN",
  running: "WORKING",
  review: "REVIEW",
  passed: "PASS",
  retry: "WORKING",
  blocked: "REVIEW",
  approval: "APPROVAL",
  merged: "PASS",
  released: "PASS",
  cancelled: "REVIEW",
};

const agentIds = new Set(["codex", "claude", "opencode", "cursor-agent"]);

async function coreRequest<T>(request: Record<string, unknown>): Promise<T> {
  const raw = await invoke<string>("core_request", { request: JSON.stringify(request) });
  const envelope = JSON.parse(raw) as CoreEnvelope<T>;
  if (!envelope.ok || envelope.result === undefined) {
    throw new Error(
      envelope.error
        ? `${envelope.error.code}: ${envelope.error.message}`
        : "Divan Core isteği başarısız",
    );
  }
  return envelope.result;
}

function App() {
  const [caps, setCaps] = useState<Capabilities | null>(null);
  const [shellCaps, setShellCaps] = useState<ShellCapabilities | null>(null);
  const [updateStatus, setUpdateStatus] = useState<UpdateStatus | null>(null);
  const [updateCheckError, setUpdateCheckError] = useState<string | null>(null);
  const [updateNotice, setUpdateNotice] = useState<string | null>(null);
  const [readiness, setReadiness] = useState<Readiness | null>(null);
  const [projects, setProjects] = useState<ProjectRecord[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [tasks, setTasks] = useState<CoreTask[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [evidence, setEvidence] = useState<EvidenceRecord[]>([]);
  const [taskDiff, setTaskDiff] = useState<TaskDiff | null>(null);
  const [pluginInspection, setPluginInspection] = useState<PluginInspection | null>(null);
  const [agent, setAgent] = useState<string>("");
  const [engine, setEngine] = useState<string>("");
  const [activeTab, setActiveTab] = useState<ActiveTab>("taht");
  const [arsenalView, setArsenalView] = useState<"plugins" | "tools">("plugins");
  const [depth, setDepth] = useState<Depth>("padisah");
  const [doctor, setDoctor] = useState<DoctorPayload | null>(null);
  const [agencyStatus, setAgencyStatus] = useState<AgencyStatus | null>(null);
  const [firstRunDone, setFirstRunDone] = useState<boolean>(readFirstRunDone);
  const [firstRunError, setFirstRunError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refreshReadiness = async () => {
    const value = await coreRequest<Readiness>({ command: "readiness" });
    setReadiness(value);
    setAgent((current) => current || value.recommended_agent || "");
  };

  const refreshDoctor = async () => {
    const value = await coreRequest<DoctorPayload>({ command: "doctor" });
    setDoctor(value);
  };

  const refreshProjects = async () => {
    const value = await coreRequest<ProjectRecord[]>({ command: "project.list" });
    setProjects(value);
    setSelectedProjectId((current) => current ?? value[0]?.project_id ?? null);
  };

  const refreshTasks = async () => {
    const value = await coreRequest<CoreTask[]>({ command: "task.list" });
    setTasks(value);
    setSelectedId((current) => current ?? value[0]?.task_id ?? null);
  };

  useEffect(() => {
    Promise.all([
      coreRequest<Capabilities>({ command: "capabilities" }),
      invoke<ShellCapabilities>("divan_capabilities"),
      refreshReadiness(),
      refreshProjects(),
      refreshTasks(),
    ])
      .then(([capabilities, shellCapabilities]) => {
        setCaps(capabilities);
        setShellCaps(shellCapabilities);
      })
      .catch((value: unknown) => setError(String(value)));
    // The doctor probes tools out of process and may take a while; it must
    // not hold the rest of the shell hostage.
    refreshDoctor().catch(() => setDoctor(null));
  }, []);

  const selected = useMemo(
    () => tasks.find((task) => task.task_id === selectedId) ?? tasks[0] ?? null,
    [tasks, selectedId],
  );
  const selectedProject = useMemo(
    () => projects.find((project) => project.project_id === selectedProjectId) ?? null,
    [projects, selectedProjectId],
  );
  const availableEngines = readiness?.engines ?? [];
  const operatorEngine = engine && availableEngines.includes(engine) ? engine : "";
  const persistedTaskEngine =
    selected?.engine_id && availableEngines.includes(selected.engine_id)
      ? selected.engine_id
      : "";
  const selectedEngine =
    operatorEngine || persistedTaskEngine || readiness?.recommended_engine || "";
  const selectedState = selected ? stateMap[selected.state] ?? "PLAN" : "PLAN";
  const canReadDiff = Boolean(
    selected && !["draft", "planned"].includes(selected.state),
  );
  const hasExecutionReceipt = Boolean(
    selected
      && typeof selected.metadata.execution === "object"
      && selected.metadata.execution !== null,
  );
  const interruptedExecution = Boolean(
    selected?.state === "running" && !hasExecutionReceipt,
  );
  const navItemClass = (item: NavItem) =>
    item.group.includes(activeTab) ? "nav-item active" : "nav-item";
  const patronDepth = depth === "padisah";

  useEffect(() => {
    if (!selectedProject) {
      setAgencyStatus(null);
      return;
    }
    coreRequest<AgencyStatus>({
      command: "project.agency.status",
      project_id: selectedProject.project_id,
    })
      .then(setAgencyStatus)
      .catch(() => setAgencyStatus(null));
  }, [selectedProject?.project_id, tasks]);

  useEffect(() => {
    if (!selected) {
      setEvidence([]);
      return;
    }
    coreRequest<EvidenceRecord[]>({ command: "evidence.list", task_id: selected.task_id })
      .then(setEvidence)
      .catch(() => setEvidence([]));
  }, [selectedId, selected?.state]);

  useEffect(() => {
    if (!selected || !canReadDiff || interruptedExecution) {
      setTaskDiff(null);
      return;
    }
    coreRequest<TaskDiff>({ command: "task.diff", task_id: selected.task_id })
      .then(setTaskDiff)
      .catch(() => setTaskDiff(null));
  }, [selectedId, selected?.state, canReadDiff, interruptedExecution]);

  const run = async (label: string, action: () => Promise<void>) => {
    setBusy(label);
    setError(null);
    try {
      await action();
    } catch (value) {
      setError(String(value));
    } finally {
      setBusy(null);
    }
  };

  const addProject = () =>
    run("project", async () => {
      const selectedFolder = await open({
        directory: true,
        multiple: false,
        title: "Divan için Git proje klasörünü seç",
      });
      if (typeof selectedFolder !== "string" || !selectedFolder.trim()) return;
      const project = await coreRequest<ProjectRecord>({
        command: "project.register",
        root: selectedFolder.trim(),
      });
      await refreshProjects();
      setSelectedProjectId(project.project_id);
    });

  const completeFirstRun = (workspacePath: string) =>
    run("first-run", async () => {
      setFirstRunError(null);
      try {
        const project = await coreRequest<ProjectRecord>({
          command: "project.register",
          root: workspacePath,
        });
        await refreshProjects();
        setSelectedProjectId(project.project_id);
      } catch (value) {
        setFirstRunError(String(value));
        return;
      }
      // "First run done" is persisted by the shell, never by the wizard.
      writeFirstRunDone();
      setFirstRunDone(true);
      setActiveTab("taht");
    });

  const inspectPlugin = () =>
    run("plugin-inspect", async () => {
      const selectedManifest = await open({
        directory: false,
        multiple: false,
        title: "Divan plugin manifestini seç",
        filters: [{ name: "Divan Plugin Manifest", extensions: ["json"] }],
      });
      if (typeof selectedManifest !== "string" || !selectedManifest.trim()) return;
      const inspection = await coreRequest<PluginInspection>({
        command: "plugin.inspect",
        manifest_path: selectedManifest.trim(),
      });
      setPluginInspection(inspection);
      setActiveTab("plugins");
    });

  const createTask = () =>
    run("create", async () => {
      const title = window.prompt("Divan ne yapsın?");
      if (!title?.trim()) return;
      const created = await coreRequest<CoreTask>({
        command: "task.create",
        title: title.trim(),
        project_id: selectedProject?.project_id ?? undefined,
        engine_id: operatorEngine || undefined,
      });
      await refreshTasks();
      setSelectedId(created.task_id);
    });

  const planTask = () =>
    selected &&
    run("plan", async () => {
      await coreRequest<CoreTask>({
        command: "task.plan",
        task_id: selected.task_id,
        reason: "operator requested plan",
      });
      await refreshTasks();
    });

  const startTask = () =>
    selected &&
    run("start", async () => {
      const executionEngine =
        operatorEngine || persistedTaskEngine || readiness?.recommended_engine || "";
      const confirmed = window.confirm(
        `Divan bu görevi izole bir Git worktree içinde çalıştıracak.\n\nGörev: ${selected.title}\nAjan: ${agent || "otomatik"}\nMotor: ${executionEngine || "otomatik"}\n\nBir kez çalıştırmayı onaylıyor musun?`,
      );
      if (!confirmed) return;
      await coreRequest<CoreTask>({
        command: "task.start",
        task_id: selected.task_id,
        approve_execution: true,
        agent: agent || undefined,
        engine_id: executionEngine || undefined,
        prompt: selected.title,
      });
      await refreshTasks();
    });

  const recoverInterruptedTask = () =>
    selected &&
    run("recover", async () => {
      await coreRequest<CoreTask>({
        command: "task.recover.interrupted",
        task_id: selected.task_id,
      });
      await refreshTasks();
    });

  const refreshDiff = () =>
    selected &&
    run("diff", async () => {
      const value = await coreRequest<TaskDiff>({
        command: "task.diff",
        task_id: selected.task_id,
      });
      setTaskDiff(value);
    });

  const reviewTask = () =>
    selected &&
    run("review", async () => {
      const value = await coreRequest<ReviewResult>({
        command: "task.review.auto",
        task_id: selected.task_id,
      });
      await refreshTasks();
      setSelectedId(value.task.task_id);
      setActiveTab(value.review.verdict === "pass" ? "summary" : "evidence");
    });

  const requestApproval = () =>
    selected &&
    run("approval", async () => {
      await coreRequest<CoreTask>({
        command: "task.approval.request",
        task_id: selected.task_id,
      });
      await refreshTasks();
    });

  const approveMerge = () =>
    selected &&
    run("approve", async () => {
      const confirmed = window.confirm(
        "Review PASS. Bu görevin merge onayını gerçekten vermek istiyor musun?",
      );
      if (!confirmed) return;
      await coreRequest<CoreTask>({
        command: "task.approve",
        task_id: selected.task_id,
        approved: true,
      });
      await refreshTasks();
    });

  const releaseTask = () =>
    selected &&
    run("release", async () => {
      await coreRequest<CoreTask>({
        command: "task.release",
        task_id: selected.task_id,
      });
      await refreshTasks();
    });

  const checkForUpdate = async () => {
    setBusy("update-check");
    setError(null);
    setUpdateCheckError(null);
    setUpdateNotice(null);
    setUpdateStatus(null);
    try {
      const status = await invoke<UpdateStatus>("check_for_update");
      setUpdateStatus(status);
    } catch (value) {
      const message = String(value);
      setUpdateCheckError(
        "Güncelleme kontrolü tamamlanamadı. Önceki sonuç güvenlik nedeniyle geçersiz sayıldı; yeniden kontrol et.",
      );
      setError(message);
    } finally {
      setBusy(null);
    }
  };

  const installUpdate = () =>
    run("update-install", async () => {
      if (!updateStatus?.available) return;
      const confirmed = window.confirm(
        `İmzalı Divan ${updateStatus.version ?? "güncellemesi"} indirilecek, doğrulanacak, kurulacak ve uygulama yeniden başlatılacak. Devam edilsin mi?`,
      );
      if (!confirmed) return;
      setUpdateNotice(null);
      const result = await invoke<UpdateInstallStatus>("install_update", { approved: true });
      if (!result.installed) {
        setUpdateStatus(null);
        setUpdateNotice(
          "Güncelleme ikinci kontrolde artık mevcut değildi. Hiçbir paket kurulmadı; tekrar kontrol et.",
        );
      }
    });

  const apiVersion = caps?.api_version ?? caps?.apiVersion ?? 1;

  if (!firstRunDone) {
    return (
      <main className="app-shell first-run-shell">
        <FirstRunWizard
          doctor={doctor}
          onCheck={() => run("doctor", refreshDoctor)}
          onComplete={completeFirstRun}
          notice={
            firstRunError
              ? "Bu klasör kaydedilemedi. Divan yalnız bir Git deposu kökünü kabul eder; başka bir klasör seçin."
              : error
                ? "Divan Core'a şu an ulaşılamıyor; kontrol sonuçları gelmeyebilir."
                : null
          }
        />
      </main>
    );
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="seal">D</span>
          <strong>DİVAN</strong>
        </div>
        <div className="project-pill">
          {selectedProject
            ? patronDepth
              ? selectedProject.name
              : selectedProject.root
            : "Proje seçilmedi"}
        </div>
        <div className="depth-switch" role="group" aria-label="Ayrıntı düzeyi">
          {DEPTH_OPTIONS.map(([value, label]) => (
            <button
              key={value}
              type="button"
              className={depth === value ? "depth-option active" : "depth-option"}
              aria-pressed={depth === value}
              onClick={() => setDepth(value)}
            >
              {label}
            </button>
          ))}
        </div>
        <div className="engine-pill">
          <span className="dot" />
          {selectedEngine ? `${selectedEngine} hazır` : "motor aranıyor"}
        </div>
      </header>

      <aside className="sidebar">
        <div>
          <nav aria-label="Ana gezinti">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.tab}
                className={navItemClass(item)}
                onClick={() => setActiveTab(item.tab)}
              >
                {item.label}
              </button>
            ))}
          </nav>

          <section className="project-list">
            <span className="eyebrow">PROJELER</span>
            {projects.map((project) => (
              <button
                key={project.project_id}
                className={
                  project.project_id === selectedProjectId
                    ? "project-row selected"
                    : "project-row"
                }
                onClick={() => setSelectedProjectId(project.project_id)}
              >
                <strong>{project.name}</strong>
                {!patronDepth && <small>{project.root}</small>}
              </button>
            ))}
            <button className="secondary compact" onClick={addProject} disabled={busy !== null}>
              + Proje ekle
            </button>
          </section>
        </div>

        <section className="runtime-card">
          <span className="eyebrow">OTOMATİK KEŞİF</span>
          <strong>
            {readiness?.tools.filter((tool) => tool.available).length ?? 0}/
            {readiness?.tools.length ?? 0} araç bulundu
          </strong>
          {readiness?.tools.slice(0, 7).map((tool) => (
            <div className="tool-row" key={tool.id}>
              <span>{tool.display_name || tool.id}</span>
              <span className={tool.available ? "ok" : "muted"}>
                {tool.available ? "●" : "○"}
              </span>
            </div>
          ))}
          <button className="text-button" onClick={() => run("scan", refreshReadiness)}>
            Yeniden tara
          </button>
        </section>
      </aside>

      <section className="workspace">
        {activeTab === "taht" ? (
          <TahtView
            status={agencyStatus}
            projectId={selectedProject?.project_id ?? null}
            depth={depth}
            onDepthChange={setDepth}
            onOpenWorkPackages={() => {
              void refreshTasks();
              setActiveTab("summary");
            }}
          />
        ) : activeTab === "archive" ? (
          <ArchiveView doctor={doctor} depth={depth} onCheck={() => run("doctor", refreshDoctor)} />
        ) : activeTab === "system" ? (
          <section>
            <div className="section-heading">
              <div>
                <span className="eyebrow">SİSTEM</span>
                <h1>Bilgisayarın sağlığı</h1>
              </div>
              <button className="secondary" onClick={() => setActiveTab("releases")}>
                Sürümler ve güncelleme
              </button>
            </div>
            <DoctorPanel
              payload={doctor}
              onCheck={() => run("doctor", refreshDoctor)}
              depth={depth}
              onDepthChange={setDepth}
            />
          </section>
        ) : activeTab === "plugins" ? (
          <section>
            <div className="tabs">
              <button
                className={arsenalView === "plugins" ? "active-tab" : undefined}
                onClick={() => setArsenalView("plugins")}
              >Eklentiler</button>
              <button
                className={arsenalView === "tools" ? "active-tab" : undefined}
                onClick={() => setArsenalView("tools")}
              >
                Yönetilen araçlar
              </button>
            </div>
            {arsenalView === "plugins" ? (
              <PluginTrustCenter
                inspection={pluginInspection}
                busy={busy === "plugin-inspect"}
                onInspect={inspectPlugin}
              />
            ) : (
              <ManagedToolsView readiness={readiness} depth={depth} />
            )}
          </section>
        ) : activeTab === "settings" ? (
          <Settings
            readiness={readiness}
            agent={agent}
            setAgent={setAgent}
            engine={engine}
            setEngine={setEngine}
          />
        ) : activeTab === "releases" ? (
          <ReleaseView
            shellCaps={shellCaps}
            status={updateStatus}
            checkError={updateCheckError}
            notice={updateNotice}
            busy={busy}
            onCheck={checkForUpdate}
            onInstall={installUpdate}
          />
        ) : activeTab === "evidence" ? (
          <EvidenceView task={selected} evidence={evidence} depth={depth} />
        ) : activeTab === "diff" ? (
          <DiffView
            task={selected}
            value={taskDiff}
            busy={busy === "diff"}
            onRefresh={refreshDiff}
          />
        ) : (
          <>
            <div className="section-heading">
              <div>
                <span className="eyebrow">AKTİF GÖREVLER</span>
                <h1>Yazılım ekibi</h1>
              </div>
              <button className="primary" disabled={busy !== null} onClick={createTask}>
                {busy === "create" ? "Oluşturuluyor…" : "+ Yeni görev"}
              </button>
            </div>

            {!selectedProject && (
              <section className="notice-card">
                <strong>Önce proje ekle</strong>
                <p>
                  Divan tüm diski taramaz. Senin seçtiğin Git klasörünü kaydeder ve yalnız o
                  proje içinde çalışır.
                </p>
                <button className="primary" onClick={addProject}>Proje klasörü ekle</button>
              </section>
            )}

            {tasks.length > 0 ? (
              <div className="task-grid">
                {tasks.map((task) => {
                  const uiState = stateMap[task.state] ?? "PLAN";
                  return (
                    <button
                      key={task.task_id}
                      className={
                        selected?.task_id === task.task_id
                          ? "task-card selected"
                          : "task-card"
                      }
                      onClick={() => setSelectedId(task.task_id)}
                    >
                      <span className="task-id">{task.task_id}</span>
                      <strong>{task.title}</strong>
                      <div className="task-meta">
                        <span>{task.engine_id ?? "Motor otomatik"}</span>
                        <span className={`state ${uiState.toLowerCase()}`}>{uiState}</span>
                      </div>
                    </button>
                  );
                })}
              </div>
            ) : (
              <section className="terminal-panel empty-state">
                <span className="eyebrow">BAŞLAMAYA HAZIR</span>
                <h2>Henüz görev yok</h2>
                <p>Proje ekle, sonra “Yeni görev” ile normal Türkçe yazarak başla.</p>
              </section>
            )}

            {selected && (
              <>
                <section className="pipeline">
                  {["PLAN", "WORKING", "REVIEW", "PASS", "APPROVAL"].map((step) => (
                    <div
                      key={step}
                      className={
                        step === selectedState ? "pipeline-step current" : "pipeline-step"
                      }
                    >
                      {step}
                    </div>
                  ))}
                </section>

                <section className="terminal-panel">
                  <div className="tabs">
                    <button className="active-tab">Özet</button>
                    <button onClick={() => setActiveTab("evidence")}>Kanıtlar</button>
                    <button
                      disabled={!canReadDiff || interruptedExecution}
                      onClick={() => setActiveTab("diff")}
                    >
                      Diff
                    </button>
                    <button disabled>Terminal</button>
                  </div>
                  {interruptedExecution && (
                    <section className="notice-card">
                      <strong>Kesintiye uğramış execution bulundu.</strong>
                      <p>
                        Divan bu görevi otomatik devam ettirmedi. Önce kesintiyi RETRY durumuna
                        al; tekrar çalıştırmak istersen sonraki adımda yeniden açık onay ver.
                      </p>
                    </section>
                  )}
                  <div className="summary-grid">
                    <div>
                      <span className="eyebrow">EXECUTION ENGINE</span>
                      <strong>{selectedEngine || "bekliyor"}</strong>
                    </div>
                    <div>
                      <span className="eyebrow">AJAN</span>
                      <strong>{agent || readiness?.recommended_agent || "otomatik"}</strong>
                    </div>
                    {!patronDepth && (
                      <>
                        <div>
                          <span className="eyebrow">CORE STATE</span>
                          <strong>{selected.state}</strong>
                        </div>
                        <div>
                          <span className="eyebrow">DIVAN CORE</span>
                          <strong>API v{apiVersion}</strong>
                        </div>
                      </>
                    )}
                  </div>
                  <div className="action-row">
                    {selected.state === "draft" && (
                      <button className="primary" onClick={planTask} disabled={busy !== null}>
                        Planla
                      </button>
                    )}
                    {(selected.state === "planned" || selected.state === "retry") && (
                      <button className="primary" onClick={startTask} disabled={busy !== null}>
                        {busy === "start" ? "Ajan çalışıyor…" : "Çalıştır"}
                      </button>
                    )}
                    {interruptedExecution && (
                      <button className="primary" onClick={recoverInterruptedTask} disabled={busy !== null}>
                        {busy === "recover" ? "Kurtarılıyor…" : "Kesintiyi retry'a hazırla"}
                      </button>
                    )}
                    {(selected.state === "review" || (selected.state === "running" && !interruptedExecution)) && (
                      <button className="primary" onClick={reviewTask} disabled={busy !== null}>
                        {busy === "review" ? "Bağımsız reviewer çalışıyor…" : "Bağımsız review"}
                      </button>
                    )}
                    {selected.state === "passed" && (
                      <button className="primary" onClick={requestApproval} disabled={busy !== null}>
                        Onay kapısını aç
                      </button>
                    )}
                    {selected.state === "approval" && (
                      <button className="approve" onClick={approveMerge} disabled={busy !== null}>
                        Bir kez onayla
                      </button>
                    )}
                    {selected.state === "merged" && (
                      <button className="primary" onClick={releaseTask} disabled={busy !== null}>
                        Release kaydını tamamla
                      </button>
                    )}
                  </div>
                </section>
              </>
            )}
          </>
        )}

        {error && <p className="error">Runtime hatası: {error}</p>}
      </section>

      {activeTab === "plugins" ? (
        <PluginInspectorRail
          inspection={pluginInspection}
          busy={busy === "plugin-inspect"}
          onInspect={inspectPlugin}
        />
      ) : (
        <aside className="inspector">
          <span className="eyebrow">ONAY KAPISI</span>
          <h2>{selected?.task_id ?? "Görev seçilmedi"}</h2>
          <p>
            {selected?.title ??
              "Bir görev oluşturduğunda burada gerçek Core durumu ve kanıtları görünecek."}
          </p>
          <dl>
            <div>
              <dt>Durum</dt>
              <dd>
                {!selected
                  ? "—"
                  : patronDepth
                    ? interruptedExecution
                      ? "Kesintiye uğradı"
                      : selectedState
                    : interruptedExecution
                      ? "running / interrupted"
                      : selected.state}
              </dd>
            </div>
            <div><dt>Engine</dt><dd>{selectedEngine || "—"}</dd></div>
            <div><dt>Ajan</dt><dd>{agent || readiness?.recommended_agent || "—"}</dd></div>
            <div><dt>Kanıt</dt><dd>{evidence.length}</dd></div>
            <div><dt>Mandate</dt><dd>{selected?.mandate_id ? "Var" : "Gerekli"}</dd></div>
          </dl>
          <button
            className="secondary"
            disabled={!canReadDiff || interruptedExecution}
            onClick={() => setActiveTab("diff")}
          >
            Değişiklikleri incele
          </button>
          <button className="secondary" disabled={!selected} onClick={() => setActiveTab("evidence")}>
            Kanıtları incele
          </button>
          <button
            className="approve"
            disabled={selected?.state !== "approval" || busy !== null}
            onClick={approveMerge}
          >
            Bir kez onayla
          </button>
          <small>
            API anahtarı zorunlu değildir. Kurulu ajan kendi abonelik/oturumuyla çalışabiliyorsa
            Divan o hesabı kullanır; kimlik bilgisini kopyalamaz.
          </small>
        </aside>
      )}
      {/* The Ctrl+K quick desk: a shortcut to TAHT, following the shell depth. */}
      <PatronDesk depth={depth} />
    </main>
  );
}

function ReleaseView({
  shellCaps,
  status,
  checkError,
  notice,
  busy,
  onCheck,
  onInstall,
}: {
  shellCaps: ShellCapabilities | null;
  status: UpdateStatus | null;
  checkError: string | null;
  notice: string | null;
  busy: string | null;
  onCheck: () => void;
  onInstall: () => void;
}) {
  if (shellCaps === null) {
    return (
      <section>
        <div className="section-heading">
          <div>
            <span className="eyebrow">SÜRÜMLER / GÜNCELLEME</span>
            <h1>Divan Desktop</h1>
          </div>
        </div>
        <section className="notice-card">
          <strong>Güncelleme yetenekleri okunuyor…</strong>
          <p>Build kimliği doğrulanmadan beta veya stable kanal varsayımı yapılmaz.</p>
        </section>
      </section>
    );
  }

  const signedUpdater = shellCaps.features.includes("signed-updater");
  return (
    <section>
      <div className="section-heading">
        <div>
          <span className="eyebrow">SÜRÜMLER / GÜNCELLEME</span>
          <h1>Divan Desktop {shellCaps.version}</h1>
        </div>
      </div>

      {!signedUpdater ? (
        <section className="notice-card">
          <strong>Bu build stable updater içermiyor.</strong>
          <p>
            Beta/unsigned paketler kendini güncellemez. Stable build yalnız imzalı Tauri updater
            artefaktlarını kabul eder; güncelleme kontrolü veya kurulumu otomatik başlatılmaz.
          </p>
        </section>
      ) : (
        <>
          <section className="notice-card">
            <strong>İmzalı güncelleme kanalı etkin.</strong>
            <p>
              Divan yalnız sen istediğinde güncelleme kontrolü yapar. Kurulum ayrıca açık onay
              ister; Tauri imza doğrulaması geçmeden paket kurulmaz.
            </p>
          </section>
          <section className="terminal-panel settings-agent">
            <span className="eyebrow">UPDATE STATUS</span>
            <strong>
              {checkError
                ? "Kontrol tamamlanamadı"
                : status === null
                  ? "Henüz kontrol edilmedi"
                  : status.available
                    ? `Yeni sürüm: ${status.version ?? "mevcut"}`
                    : "Bu sürüm güncel"}
            </strong>
            {checkError && <p className="error">{checkError}</p>}
            {notice && <p>{notice}</p>}
            <div className="action-row">
              <button className="primary" onClick={onCheck} disabled={busy !== null}>
                {busy === "update-check" ? "Kontrol ediliyor…" : "Güncellemeyi kontrol et"}
              </button>
              {status?.available && !checkError && (
                <button className="approve" onClick={onInstall} disabled={busy !== null}>
                  {busy === "update-install" ? "Kuruluyor…" : "İmzalı güncellemeyi yükle"}
                </button>
              )}
            </div>
          </section>
        </>
      )}
    </section>
  );
}

function Settings({
  readiness,
  agent,
  setAgent,
  engine,
  setEngine,
}: {
  readiness: Readiness | null;
  agent: string;
  setAgent: (value: string) => void;
  engine: string;
  setEngine: (value: string) => void;
}) {
  const agents = readiness?.tools.filter((tool) => agentIds.has(tool.id) && tool.available) ?? [];
  const engines = readiness?.engines ?? [];
  return (
    <section>
      <div className="section-heading">
        <div>
          <span className="eyebrow">İLK KURULUM / AYARLAR</span>
          <h1>Bilgisayardaki araçlar</h1>
        </div>
      </div>

      <section className="notice-card">
        <strong>API anahtarı bilmek zorunda değilsin.</strong>
        <p>
          Codex, Claude Code, Cursor Agent veya diğer desteklenen araçlarda hesabın açıksa
          Divan önce o mevcut oturumu kullanır. API anahtarı yalnız isteyen ileri kullanıcı
          için ek yöntemdir.
        </p>
      </section>

      <div className="settings-grid">
        {readiness?.tools.map((tool) => (
          <article className="settings-card" key={tool.id}>
            <div className="settings-title">
              <strong>{tool.display_name || tool.id}</strong>
              <span className={tool.available ? "ok-text" : "muted"}>
                {tool.available ? "Bulundu" : "Bulunamadı"}
              </span>
            </div>
            <small>{tool.version ?? tool.app_version ?? "Sürüm bilgisi yok"}</small>
            <dl>
              <div><dt>CLI</dt><dd>{tool.path ? "Var" : "Yok"}</dd></div>
              <div><dt>Masaüstü</dt><dd>{tool.app_installed ? "Var" : "—"}</dd></div>
              <div><dt>Oturum</dt><dd>{authLabel(tool)}</dd></div>
              <div><dt>API env</dt><dd>{tool.api_key_configured ? "Var" : "Gerekli değil"}</dd></div>
            </dl>
          </article>
        ))}
      </div>

      <section className="terminal-panel settings-agent">
        <span className="eyebrow">VARSAYILAN EXECUTION ENGINE</span>
        <select value={engine} onChange={(event) => setEngine(event.target.value)}>
          <option value="">Otomatik seç</option>
          {engines.map((engineId) => (
            <option value={engineId} key={engineId}>{engineId}</option>
          ))}
        </select>
        <p>
          Native ve Orca aynı Divan execution contract arkasındadır. Açık bir seçim yaparsan
          planlanmış görevde de bu seçim önceliklidir; Otomatik seçiliyse yalnız hâlâ kullanılabilir
          kayıtlı motor veya Divan'ın güncel önerisi kullanılır.
        </p>
      </section>

      <section className="terminal-panel settings-agent">
        <span className="eyebrow">VARSAYILAN İŞÇİ</span>
        <select value={agent} onChange={(event) => setAgent(event.target.value)}>
          <option value="">Otomatik seç</option>
          {agents.map((tool) => (
            <option value={tool.id} key={tool.id}>{tool.display_name}</option>
          ))}
        </select>
        <p>
          Divan Codex → Claude → OpenCode → Cursor Agent sırasını yalnız kullanılabilir
          araçlardan seçer. Seçimi istediğin zaman değiştirebilirsin.
        </p>
      </section>
    </section>
  );
}

/**
 * TAHT: the Patron's default screen. One desk (the same PatronDeskPanel the
 * Ctrl+K dialog shows) and one status card read from `project.agency.status`.
 * Nothing here is computed on the client; the summary lists only fields the
 * Core payload carries.
 */
function TahtView({
  status,
  projectId,
  depth,
  onDepthChange,
  onOpenWorkPackages,
}: {
  status: AgencyStatus | null;
  projectId: string | null;
  depth: Depth;
  onDepthChange: (depth: Depth) => void;
  onOpenWorkPackages: () => void;
}) {
  return (
    <section className="taht">
      <div className="section-heading">
        <div>
          <span className="eyebrow">TAHT</span>
          <h1>Patron Masası</h1>
        </div>
      </div>

      {status ? (
        <>
          <section className="patron-summary" aria-label="Proje özeti">
            <dl>
              {patronSummary(status).map((field) => (
                <div key={field.id} data-field={field.id}>
                  <dt>{field.label}</dt>
                  <dd>{field.value}</dd>
                </div>
              ))}
            </dl>
          </section>
          <ProjectStatusCard status={status} depth={depth} onDepthChange={onDepthChange} />
        </>
      ) : projectId ? (
        <section className="notice-card">
          <strong>Proje durumu okunuyor…</strong>
          <p>Divan bu projenin gerçek durumunu Core'dan okumadan hiçbir özet göstermez.</p>
        </section>
      ) : null}

      <PatronDeskPanel
        depth={depth}
        projectId={projectId}
        onOpenWorkPackages={onOpenWorkPackages}
      />
    </section>
  );
}

const ARCHIVE_CAPABILITIES: ReadonlyArray<[string, string]> = [
  ["memory-store", "Hafıza deposu"],
  ["memory-recall", "Hafıza geri çağırma"],
];

/**
 * ARŞİV: there is no memory browsing screen yet, so this shows only what the
 * Core doctor says about the memory capabilities. No sample data, no counts
 * the Core did not report.
 */
function ArchiveView({
  doctor,
  depth,
  onCheck,
}: {
  doctor: DoctorPayload | null;
  depth: Depth;
  onCheck: () => void;
}) {
  return (
    <section>
      <div className="section-heading">
        <div>
          <span className="eyebrow">ARŞİV</span>
          <h1>Divan'ın hafızası</h1>
        </div>
        <button className="secondary" onClick={onCheck}>Yeniden kontrol et</button>
      </div>
      <section className="notice-card">
        <strong>Hafıza görüntüleme ekranı henüz yok.</strong>
        <p>
          Burada yalnız Core'un hafıza yetenekleri hakkında söylediği görünür; kayıtlar
          listelenmez ve sayı uydurulmaz.
        </p>
      </section>
      <ul className="archive-lines">
        {ARCHIVE_CAPABILITIES.map(([id, title]) => {
          const capability = doctor?.capabilities.find((item) => item.capability_id === id);
          const line = capability ? capabilityLine(capability) : pendingLine(title);
          return (
            <li key={id} data-tone={line.tone}>
              <span className="wizard-line" data-tone={line.tone}>
                {`${line.glyph} ${line.sentence}`}
              </span>
              {depth === "teknik" && capability && (
                <small>
                  {[capability.state, capability.code, capability.detail, capability.evidence]
                    .filter((part): part is string => Boolean(part))
                    .join(" · ")}
                </small>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}

/** CEPHANELİK, second tab: the tools Divan found, without paths at the Patron. */
function ManagedToolsView({
  readiness,
  depth,
}: {
  readiness: Readiness | null;
  depth: Depth;
}) {
  return (
    <section>
      <div className="section-heading">
        <div>
          <span className="eyebrow">YÖNETİLEN ARAÇLAR</span>
          <h1>Bilgisayarda bulunan araçlar</h1>
        </div>
      </div>
      {!readiness ? (
        <section className="notice-card">
          <strong>Araçlar henüz taranmadı.</strong>
        </section>
      ) : (
        <div className="settings-grid">
          {readiness.tools.map((tool) => (
            <article className="settings-card" key={tool.id}>
              <div className="settings-title">
                <strong>{tool.display_name || tool.id}</strong>
                <span className={tool.available ? "ok-text" : "muted"}>
                  {tool.available ? "Bulundu" : "Bulunamadı"}
                </span>
              </div>
              <small>{tool.version ?? tool.app_version ?? "Sürüm bilgisi yok"}</small>
              {depth === "teknik" && tool.path && <code>{tool.path}</code>}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

function EvidenceView({
  task,
  evidence,
  depth,
}: {
  task: CoreTask | null;
  evidence: EvidenceRecord[];
  depth: Depth;
}) {
  return (
    <section>
      <div className="section-heading">
        <div>
          <span className="eyebrow">KANIT DEFTERİ</span>
          <h1>{task ? (depth === "padisah" ? task.title : task.task_id) : "Görev seçilmedi"}</h1>
        </div>
      </div>
      {evidence.length === 0 ? (
        <section className="notice-card">
          <strong>Henüz kanıt yok</strong>
          <p>Execution, review, approval ve release kayıtları burada SHA-256 ile görünür.</p>
        </section>
      ) : (
        <div className="evidence-list">
          {evidence.map((item) => (
            <article className="evidence-card" key={`${item.at}-${item.kind}`}>
              <div>
                <span className="eyebrow">{item.kind.toUpperCase()}</span>
                <strong>{item.summary}</strong>
              </div>
              <span className={item.status === "pass" ? "ok-text" : "review-text"}>
                {item.status}
              </span>
              <small>{new Date(item.at).toLocaleString()}</small>
              {depth !== "padisah" && <code>{item.sha256.slice(0, 16)}…</code>}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

function DiffView({
  task,
  value,
  busy,
  onRefresh,
}: {
  task: CoreTask | null;
  value: TaskDiff | null;
  busy: boolean;
  onRefresh: () => void;
}) {
  return (
    <section>
      <div className="section-heading">
        <div>
          <span className="eyebrow">DEĞİŞİKLİKLER</span>
          <h1>{task?.task_id ?? "Görev seçilmedi"}</h1>
        </div>
        <button
          className="primary"
          disabled={!task || busy}
          onClick={onRefresh}
        >
          {busy ? "Okunuyor…" : "Diff'i yenile"}
        </button>
      </div>
      {!value ? (
        <section className="notice-card">
          <strong>Henüz okunabilir diff yok</strong>
          <p>Görev çalıştıktan sonra worker worktree değişiklikleri burada salt-okunur görünür.</p>
        </section>
      ) : (
        <section className="terminal-panel diff-panel">
          <div className="diff-meta">
            <span>{value.engine}</span>
            <span>{value.ok ? "Diff okundu" : `Exit ${value.exit_code}`}</span>
          </div>
          <pre className="diff-code">
            <code>{value.diff || "Değişiklik yok."}</code>
          </pre>
        </section>
      )}
    </section>
  );
}

function authLabel(tool: ToolStatus) {
  if (!tool.available) return "—";
  if (tool.auth === "connected") {
    if (tool.auth_detail === "chatgpt") return "ChatGPT ile bağlı";
    if (tool.auth_detail === "cursor-account") return "Cursor hesabı bağlı";
    if (tool.auth_detail === "github-account") return "GitHub bağlı";
    if (tool.auth_detail === "provider-auth") return "Sağlayıcı bağlı";
    if (tool.auth_detail === "api-key-env") return "API env ile bağlı";
    return "Bağlı";
  }
  if (tool.auth === "not-connected") return "Giriş gerekli";
  return tool.subscription_supported ? "İlk kullanımda kontrol" : "Bilinmiyor";
}

export default App;
