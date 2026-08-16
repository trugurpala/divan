import { useEffect, useMemo, useState, type FormEvent } from "react";
import { invoke } from "@tauri-apps/api/core";
import { open } from "@tauri-apps/plugin-dialog";

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

type PromptSummary = {
  id: string;
  title: string;
  preview: string;
  for_developers: boolean;
  type: string;
  contributor: string;
};

type PromptDetail = PromptSummary & {
  prompt: string;
  source: { repository: string; commit: string; license: string; dataset: string };
};

type PromptSearchResult = {
  items: PromptSummary[];
  total: number;
  source: PromptDetail["source"];
};

type LocalAiStatus = {
  available: boolean;
  endpoint: string;
  default_model: string;
  models: Array<{ name: string; size: string; modified_at: string }>;
  message: string | null;
};

type LocalAiDraft = {
  model: string;
  draft: string;
  executed: boolean;
};

type OrduPlan = {
  title: string;
  max_parallel_workers: number;
  units: Array<{ id: string; role: string; title: string; depends_on: string[] }>;
  execution: string;
  approval_required_before_mutation: boolean;
};

function taskInstruction(task: CoreTask): string {
  const promptLibrary = task.metadata.prompt_library;
  if (typeof promptLibrary === "object" && promptLibrary !== null) {
    const value = (promptLibrary as { prompt?: unknown }).prompt;
    if (typeof value === "string" && value.trim()) return value;
  }
  return task.title;
}

type ReviewResult = {
  task: CoreTask;
  review: {
    verdict: string;
    checks: Array<Record<string, unknown>>;
    reasons: string[];
  };
};

type UiState = "PLAN" | "WORKING" | "REVIEW" | "PASS" | "APPROVAL";
type ActiveTab = "summary" | "library" | "workbench" | "ordu" | "evidence" | "diff" | "releases" | "settings";

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

function isDesktopRuntime() {
  return typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
}

function mockCoreRequest<T>(request: Record<string, unknown>): T {
  switch (request.command) {
    case "capabilities":
      return {
        product: "Ottoman",
        api_version: 1,
        features: ["browser-preview"],
        commands: [],
      } as T;
    case "readiness":
      return {
        ready: false,
        tools: [],
        engines: [],
        recommended_engine: null,
        recommended_agent: null,
        api_keys_required: false,
      } as T;
    case "project.list":
    case "task.list":
    case "evidence.list":
      return [] as T;
    case "prompt.search":
      return {
        items: [
          {
            id: "browser-preview",
            title: "Prompt kütüphanesi masaüstünde açılır",
            preview: "Gerçek prompt araması Ottoman Core ile yapılır.",
            for_developers: true,
            type: "TEXT",
            contributor: "Ottoman preview",
          },
        ],
        total: 0,
        source: {
          repository: "https://github.com/f/prompts.chat",
          commit: "browser-preview",
          license: "CC0-1.0",
          dataset: "prompts.csv",
        },
      } as T;
    case "local_ai.status":
      return {
        available: false,
        endpoint: "http://127.0.0.1:11434",
        default_model: "qwen3:8b",
        models: [],
        message: "Tarayıcı önizlemesinde yerel AI servisi okunmaz.",
      } as T;
    case "local_ai.draft":
      return {
        model: "qwen3:8b",
        draft: "Tarayıcı önizlemesinde örnek taslak: kapsamı çıkar, küçük değişikliklerle ilerle, sonra test ve build kanıtını kontrol et.",
        executed: false,
      } as T;
    case "ordu.plan":
      return {
        title: String(request.title ?? "Örnek Ottoman görevi"),
        max_parallel_workers: 4,
        units: [],
        execution: "planned-only",
        approval_required_before_mutation: true,
      } as T;
    default:
      throw new Error("Bu işlem için Ottoman masaüstü runtime gerekir.");
  }
}

async function invokeCommand<T>(command: string, args?: Record<string, unknown>): Promise<T> {
  if (!isDesktopRuntime() && command === "divan_capabilities") {
    return {
      product: "Ottoman",
      version: "1.3.8",
      apiVersion: 1,
      shell: "browser-preview",
      features: [],
    } as T;
  }
  return invoke<T>(command, args);
}

async function coreRequest<T>(request: Record<string, unknown>): Promise<T> {
  if (!isDesktopRuntime()) return mockCoreRequest<T>(request);

  const raw = await invokeCommand<string>("core_request", { request: JSON.stringify(request) });
  const envelope = JSON.parse(raw) as CoreEnvelope<T>;
  if (!envelope.ok || envelope.result === undefined) {
    throw new Error(
      envelope.error
        ? `${envelope.error.code}: ${envelope.error.message}`
        : "Ottoman Core isteği başarısız",
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
  const [promptQuery, setPromptQuery] = useState("");
  const [promptResults, setPromptResults] = useState<PromptSearchResult | null>(null);
  const [selectedPrompt, setSelectedPrompt] = useState<PromptDetail | null>(null);
  const [localAi, setLocalAi] = useState<LocalAiStatus | null>(null);
  const [orduPlan, setOrduPlan] = useState<OrduPlan | null>(null);
  const [agent, setAgent] = useState<string>("");
  const [engine, setEngine] = useState<string>("");
  const [activeTab, setActiveTab] = useState<ActiveTab>("summary");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refreshReadiness = async () => {
    const value = await coreRequest<Readiness>({ command: "readiness" });
    setReadiness(value);
    setAgent((current) => current || value.recommended_agent || "");
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
      invokeCommand<ShellCapabilities>("divan_capabilities"),
      refreshReadiness(),
      refreshProjects(),
      refreshTasks(),
      coreRequest<LocalAiStatus>({ command: "local_ai.status" }),
    ])
      .then(([capabilities, shellCapabilities, , , , localAiStatus]) => {
        setCaps(capabilities);
        setShellCaps(shellCapabilities);
        setLocalAi(localAiStatus);
      })
      .catch((value: unknown) => setError(String(value)));
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
  const selectedAgent = agent || readiness?.recommended_agent || "";
  const selectedAgentTool = readiness?.tools.find((tool) => tool.id === selectedAgent);
  const executionAgentReady = Boolean(
    selectedAgentTool?.available && selectedAgentTool.auth === "connected",
  );
  const executionStartBlocked =
    busy !== null || !selectedEngine || !executionAgentReady;
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

  useEffect(() => {
    if (!selected) {
      setOrduPlan(null);
      return;
    }
    coreRequest<OrduPlan>({ command: "ordu.plan", title: selected.title })
      .then(setOrduPlan)
      .catch(() => setOrduPlan(null));
  }, [selected?.task_id, selected?.title]);

  const run = async <T,>(label: string, action: () => Promise<T>): Promise<T | undefined> => {
    setBusy(label);
    setError(null);
    try {
      return await action();
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
        title: "Ottoman için Git proje klasörünü seç",
      });
      if (typeof selectedFolder !== "string" || !selectedFolder.trim()) return;
      const project = await coreRequest<ProjectRecord>({
        command: "project.register",
        root: selectedFolder.trim(),
      });
      await refreshProjects();
      setSelectedProjectId(project.project_id);
    });

  const createTask = () =>
    run("create", async () => {
      const title = window.prompt("Ottoman ne yapsın?");
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
      if (!executionAgentReady) {
        throw new Error("Seçilen ajan kurulu ve oturum açmış değil; worktree oluşturulmadı.");
      }
      if (!selectedEngine) {
        throw new Error("Kullanılabilir bir execution engine seçilmedi; worktree oluşturulmadı.");
      }
      const confirmed = window.confirm(
        `Ottoman bu görevi izole bir Git worktree içinde çalıştıracak.\n\nGörev: ${selected.title}\nAjan: ${selectedAgent}\nMotor: ${selectedEngine}\n\nBir kez çalıştırmayı onaylıyor musun?`,
      );
      if (!confirmed) return;
      await coreRequest<CoreTask>({
        command: "task.start",
        task_id: selected.task_id,
        approve_execution: true,
        agent: selectedAgent,
        engine_id: selectedEngine,
        prompt: taskInstruction(selected),
      });
      await refreshTasks();
    });

  const searchPrompts = (query = promptQuery) =>
    run("prompt-search", async () => {
      const result = await coreRequest<PromptSearchResult>({
        command: "prompt.search",
        query,
        limit: 30,
      });
      setPromptResults(result);
      setSelectedPrompt(null);
    });

  const openPrompt = (promptId: string) =>
    run("prompt-detail", async () => {
      const result = await coreRequest<PromptDetail>({ command: "prompt.get", prompt_id: promptId });
      setSelectedPrompt(result);
    });

  const createTaskFromPrompt = () =>
    selectedPrompt &&
    run("prompt-create", async () => {
      const created = await coreRequest<CoreTask>({
        command: "task.create_from_prompt",
        prompt_id: selectedPrompt.id,
        project_id: selectedProject?.project_id ?? undefined,
        engine_id: operatorEngine || undefined,
      });
      await refreshTasks();
      setSelectedId(created.task_id);
      setActiveTab("summary");
    });

  const draftWithLocalAi = (prompt: string) =>
    run("local-ai-draft", () =>
      coreRequest<LocalAiDraft>({
        command: "local_ai.draft",
        prompt,
      }),
    );

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
        `İmzalı Ottoman ${updateStatus.version ?? "güncellemesi"} indirilecek, doğrulanacak, kurulacak ve uygulama yeniden başlatılacak. Devam edilsin mi?`,
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

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="seal">O</span>
          <strong>OTTOMAN</strong>
        </div>
        <div className="project-pill">{selectedProject?.root ?? "Proje seçilmedi"}</div>
        <div className="engine-pill">
          <span className="dot" />
          {selectedEngine ? `${selectedEngine} hazır` : "motor aranıyor"}
        </div>
      </header>

      <aside className="sidebar">
        <div>
          <nav>
            <button className="nav-item" onClick={addProject}>Projeler</button>
            <button className={activeTab === "summary" ? "nav-item active" : "nav-item"} onClick={() => setActiveTab("summary")}>Görevler</button>
            <button className="nav-item" onClick={() => setActiveTab("library")}>Prompt kütüphanesi</button>
            <button className="nav-item" onClick={() => setActiveTab("workbench")}>Yerel AI</button>
            <button className="nav-item" onClick={() => setActiveTab("ordu")}>Ordu planı</button>
            <button className="nav-item" onClick={() => setActiveTab("settings")}>Ajanlar</button>
            <button className="nav-item" onClick={() => setActiveTab("evidence")}>Kanıtlar</button>
            <button
              className="nav-item"
              disabled={!canReadDiff || interruptedExecution}
              onClick={() => setActiveTab("diff")}
            >
              Değişiklikler
            </button>
            <button className="nav-item" onClick={() => setActiveTab("releases")}>Sürümler</button>
            <button className="nav-item" onClick={() => setActiveTab("settings")}>Ayarlar</button>
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
                <small>{project.root}</small>
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
        {activeTab === "library" ? (
          <PromptLibrary
            query={promptQuery}
            setQuery={setPromptQuery}
            result={promptResults}
            selected={selectedPrompt}
            busy={busy}
            hasProject={Boolean(selectedProject)}
            onSearch={() => searchPrompts()}
            onSelect={openPrompt}
            onCreate={createTaskFromPrompt}
          />
        ) : activeTab === "workbench" ? (
          <LocalAiWorkbench
            localAi={localAi}
            busy={busy === "local-ai-draft"}
            onDraft={draftWithLocalAi}
          />
        ) : activeTab === "settings" ? (
          <Settings
            readiness={readiness}
            localAi={localAi}
            agent={agent}
            setAgent={setAgent}
            engine={engine}
            setEngine={setEngine}
          />
        ) : activeTab === "ordu" ? (
          <OrduView plan={orduPlan} task={selected} evidence={evidence} />
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
          <EvidenceView task={selected} evidence={evidence} />
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
                  Ottoman tüm diski taramaz. Senin seçtiğin Git klasörünü kaydeder ve yalnız o
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
                        Ottoman bu görevi otomatik devam ettirmedi. Önce kesintiyi RETRY durumuna
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
                    <div>
                      <span className="eyebrow">CORE STATE</span>
                      <strong>{selected.state}</strong>
                    </div>
                    <div>
                      <span className="eyebrow">OTTOMAN CORE</span>
                      <strong>API v{apiVersion}</strong>
                    </div>
                  </div>
                  <div className="action-row">
                    {selected.state === "draft" && (
                      <button className="primary" onClick={planTask} disabled={busy !== null}>
                        Planla
                      </button>
                    )}
                    {(selected.state === "planned" || selected.state === "retry") && (
                      <button className="primary" onClick={startTask} disabled={executionStartBlocked}>
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

      <aside className="inspector">
        <span className="eyebrow">ONAY KAPISI</span>
        <h2>{selected?.task_id ?? "Görev seçilmedi"}</h2>
        <p>
          {selected?.title ??
            "Bir görev oluşturduğunda burada gerçek durum ve kanıtlar görünecek."}
        </p>
        <dl>
          <div><dt>Durum</dt><dd>{interruptedExecution ? "running / interrupted" : selected?.state ?? "—"}</dd></div>
          <div><dt>Engine</dt><dd>{selectedEngine || "—"}</dd></div>
          <div><dt>Ajan</dt><dd>{selectedAgent || "—"}</dd></div>
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
          Ottoman o hesabı kullanır; kimlik bilgisini kopyalamaz.
        </small>
      </aside>
    </main>
  );
}

function LocalAiWorkbench({
  localAi,
  busy,
  onDraft,
}: {
  localAi: LocalAiStatus | null;
  busy: boolean;
  onDraft: (prompt: string) => Promise<LocalAiDraft | undefined>;
}) {
  const [prompt, setPrompt] = useState("");
  const [draft, setDraft] = useState<LocalAiDraft | null>(null);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!prompt.trim()) return;
    const result = await onDraft(prompt.trim());
    if (result) setDraft(result);
  };

  return (
    <section className="workbench-view">
      <div className="section-heading">
        <div>
          <span className="eyebrow">YEREL AI ÇALIŞMA MASASI</span>
          <h1>Taslak üret, önce sen incele</h1>
        </div>
      </div>
      <section className="notice-card">
        <strong>Bu alan bir çalışma taslağı üretir; hiçbir şey çalıştırmaz.</strong>
        <p>
          Metin yalnız bilgisayarındaki Ollama servisine gider. Ottoman burada terminal komutu,
          dosya değişikliği, Git işlemi veya ajan çalıştırma yapmaz. Uygulamaya geçmek istersen
          taslağı kendi seçtiğin göreve dönüştürüp normal plan ve açık onay akışını kullanırsın.
        </p>
      </section>
      <div className="workbench-layout">
        <form className="local-ai-form terminal-panel" onSubmit={submit}>
          <label htmlFor="local-ai-prompt">Ne üzerinde düşünelim?</label>
          <textarea
            id="local-ai-prompt"
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            maxLength={12000}
            placeholder="Ör. Ottoman ayar ekranını daha anlaşılır yapmak için önce neyi incelemeli, nasıl test etmeliyim?"
          />
          <small>{prompt.length.toLocaleString()} / 12.000 karakter</small>
          {!localAi?.available && (
            <p className="error">
              Yerel model şu an erişilebilir görünmüyor. Ollama çalıştıktan sonra tekrar dene.
            </p>
          )}
          <button
            className="primary"
            disabled={!prompt.trim() || busy || !localAi?.available}
            type="submit"
          >
            {busy ? "Yerel taslak hazırlanıyor…" : "Taslak hazırla"}
          </button>
        </form>
        <section className="draft-panel terminal-panel" aria-live="polite">
          {draft === null ? (
            <>
              <span className="eyebrow">SONUÇ</span>
              <h2>Henüz taslak yok</h2>
              <p>İsteğini yazdığında sonuç burada görünür; yürütme durumu her zaman kapalı kalır.</p>
            </>
          ) : (
            <>
              <span className="eyebrow">YEREL TASLAK</span>
              <h2>{draft.model}</h2>
              <pre className="prompt-text"><code>{draft.draft}</code></pre>
              <p className="draft-safety">
                Yürütme: {draft.executed ? "açık" : "kapalı"} · Bu yanıt tek başına görev,
                değişiklik veya onay oluşturmaz.
              </p>
            </>
          )}
        </section>
      </div>
    </section>
  );
}

function OrduView({
  plan,
  task,
  evidence,
}: {
  plan: OrduPlan | null;
  task: CoreTask | null;
  evidence: EvidenceRecord[];
}) {
  const latestReceipt = (unitId: string) =>
    evidence.filter(
      (item) => item.kind === "ordu-unit" && item.data.unit_id === unitId,
    ).at(-1);

  const statusLabel = (status: string | undefined) => {
    if (status === "pass") return "tamamlandı";
    if (status === "retry") return "yeniden denenecek";
    return "bekliyor";
  };

  return (
    <section>
      <div className="section-heading">
        <div>
          <span className="eyebrow">ORDU / YEREL ÇALIŞMA GRAFIĞI</span>
          <h1>{task?.title ?? "Önce bir görev seç"}</h1>
        </div>
      </div>
      <section className="notice-card">
        <strong>Plan görünür, yürütme onaylıdır.</strong>
        <p>
          Ordu önce kapsamı çıkarır. Plan sonrası uygulama ve kalite haritası paralel hazırlanabilir;
          hiçbir dosya değişikliği bu ekrandan veya bu planın kendisinden yapılmaz.
        </p>
      </section>
      {!plan ? (
        <section className="terminal-panel empty-state"><h2>Plan hazırlanıyor</h2><p>Bir görev seçildiğinde yerel çekirdek çalışma grafiğini oluşturur.</p></section>
      ) : (
        <section className="notice-card">
          <strong>{plan.max_parallel_workers} yerel işçi üst sınırı</strong>
          <p>İcra durumu: {plan.execution} · Değişiklik öncesi açık onay: {plan.approval_required_before_mutation ? "zorunlu" : "yok"}</p>
            <ol>
              {plan.units.map((unit) => {
                const receipt = latestReceipt(unit.id);
                return (
                  <li className="ordu-unit" key={unit.id}>
                    <div>
                      <strong>{unit.title}</strong>
                      <small>({unit.role}{unit.depends_on.length ? ` · önce: ${unit.depends_on.join(", ")}` : ""})</small>
                    </div>
                    <span className={`ordu-status ${receipt?.status ?? "pending"}`}>
                      {statusLabel(receipt?.status)}
                    </span>
                  </li>
                );
              })}
            </ol>
        </section>
      )}
    </section>
  );
}

function PromptLibrary({
  query,
  setQuery,
  result,
  selected,
  busy,
  hasProject,
  onSearch,
  onSelect,
  onCreate,
}: {
  query: string;
  setQuery: (value: string) => void;
  result: PromptSearchResult | null;
  selected: PromptDetail | null;
  busy: string | null;
  hasProject: boolean;
  onSearch: () => void;
  onSelect: (promptId: string) => void;
  onCreate: () => void;
}) {
  return (
    <section className="library-view">
      <div className="section-heading">
        <div>
          <span className="eyebrow">YEREL PROMPT KÜTÜPHANESİ</span>
          <h1>Bul, incele, göreve dönüştür</h1>
        </div>
      </div>
      <section className="notice-card">
        <strong>Akışı bozmadan kullan.</strong>
        <p>
          Bir şablon seçtiğinde Ottoman onu görev metni olarak saklar. Sonrasında aynı planla,
          aynı çalışma onayıyla ve aynı review kapısıyla devam eder.
        </p>
      </section>
      <form
        className="prompt-search"
        onSubmit={(event) => {
          event.preventDefault();
          onSearch();
        }}
      >
        <label htmlFor="prompt-query">Ne yapmak istiyorsun?</label>
        <div>
          <input
            id="prompt-query"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="ör. linux terminal, logo, react, öğretmen"
          />
          <button className="primary" disabled={busy !== null} type="submit">
            {busy === "prompt-search" ? "Aranıyor…" : "Kütüphanede ara"}
          </button>
        </div>
      </form>
      {result === null ? (
        <section className="terminal-panel empty-state">
          <span className="eyebrow">BAŞLANGIÇ</span>
          <h2>Arama ile başla</h2>
          <p>Arama, yerel CC0 kütüphanesinde yapılır; prompt metni internetten çağrılmaz.</p>
        </section>
      ) : (
        <div className="prompt-layout">
          <section className="prompt-results" aria-label="Prompt arama sonuçları">
            <p className="muted">
              {result.total > 0 ? `${result.total.toLocaleString()} yerel şablon içinden sonuçlar` : "Tarayıcı önizlemesi"}
            </p>
            {result.items.map((item) => (
              <button
                className={selected?.id === item.id ? "prompt-row selected" : "prompt-row"}
                key={item.id}
                onClick={() => onSelect(item.id)}
                disabled={busy !== null}
              >
                <span className="eyebrow">{item.type}{item.for_developers ? " · GELİŞTİRİCİ" : ""}</span>
                <strong>{item.title}</strong>
                <small>{item.preview}</small>
              </button>
            ))}
            {result.items.length === 0 && (
              <section className="notice-card"><strong>Sonuç yok</strong><p>Daha kısa veya farklı bir kelime dene.</p></section>
            )}
          </section>
          <section className="prompt-detail terminal-panel">
            {!selected ? (
              <><span className="eyebrow">ÖNİZLEME</span><h2>Bir şablon seç</h2><p>Önce metni görürsün; görev oluşmadan hiçbir ajan çalışmaz.</p></>
            ) : (
              <>
                <span className="eyebrow">SEÇİLEN ŞABLON</span>
                <h2>{selected.title}</h2>
                <p className="muted">Topluluk şablonu · {selected.type}</p>
                <pre className="prompt-text"><code>{selected.prompt}</code></pre>
                <small>
                  Kaynak: prompts.chat · {selected.source.license} · yerel kopya
                </small>
                {!hasProject && <p className="error">Göreve dönüştürmek için önce bir proje seç.</p>}
                <button className="primary" onClick={onCreate} disabled={!hasProject || busy !== null}>
                  {busy === "prompt-create" ? "Görev hazırlanıyor…" : "Bu şablondan görev oluştur"}
                </button>
              </>
            )}
          </section>
        </div>
      )}
    </section>
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
            <h1>Ottoman Desktop</h1>
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
          <h1>Ottoman Desktop {shellCaps.version}</h1>
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
              Ottoman yalnız sen istediğinde güncelleme kontrolü yapar. Kurulum ayrıca açık onay
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
  localAi,
  agent,
  setAgent,
  engine,
  setEngine,
}: {
  readiness: Readiness | null;
  localAi: LocalAiStatus | null;
  agent: string;
  setAgent: (value: string) => void;
  engine: string;
  setEngine: (value: string) => void;
}) {
  const agents = readiness?.tools.filter(
    (tool) => agentIds.has(tool.id) && tool.available && tool.auth === "connected",
  ) ?? [];
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
        <strong>Yerel AI / Ordu</strong>
        <p>
          {localAi?.available
            ? `${localAi.models.length} yerel model hazır. Varsayılan: ${localAi.default_model}. Bu katman yalnız taslak üretir; kod çalıştırmaz veya onay atlamaz.`
            : "Yerel Ollama servisi henüz erişilebilir değil. Ottoman bulut hesabın olmadan da çalışmaya devam eder."}
        </p>
        {localAi?.models.map((model) => (
          <small key={model.name}>{model.name} · {(Number(model.size) / 1_000_000_000).toFixed(1)} GB</small>
        ))}
      </section>

      <section className="notice-card">
        <strong>API anahtarı bilmek zorunda değilsin.</strong>
        <p>
          Codex, Claude Code, Cursor Agent veya diğer desteklenen araçlarda hesabın açıksa
          Ottoman önce o mevcut oturumu kullanır. API anahtarı yalnız isteyen ileri kullanıcı
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
          Native ve Orca aynı Ottoman execution contract arkasındadır. Açık bir seçim yaparsan
          planlanmış görevde de bu seçim önceliklidir; Otomatik seçiliyse yalnız hâlâ kullanılabilir
          kayıtlı motor veya Ottoman'ın güncel önerisi kullanılır.
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
          Ottoman Codex → Claude → OpenCode → Cursor Agent sırasını yalnız kurulu ve oturum
          açmış araçlardan seçer. Seçimi istediğin zaman değiştirebilirsin.
        </p>
      </section>
    </section>
  );
}

function EvidenceView({
  task,
  evidence,
}: {
  task: CoreTask | null;
  evidence: EvidenceRecord[];
}) {
  return (
    <section>
      <div className="section-heading">
        <div>
          <span className="eyebrow">KANIT DEFTERİ</span>
          <h1>{task?.task_id ?? "Görev seçilmedi"}</h1>
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
              <code>{item.sha256.slice(0, 16)}…</code>
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
    if (tool.auth_detail === "api-key-configured") return "API env doğrulanmadı";
    return "Bağlı";
  }
  if (tool.auth === "not-connected") return "Giriş gerekli";
  return tool.subscription_supported ? "İlk kullanımda kontrol" : "Bilinmiyor";
}

export default App;
