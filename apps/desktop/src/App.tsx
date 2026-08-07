import { useEffect, useMemo, useState } from "react";
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
type ActiveTab = "summary" | "evidence" | "diff" | "settings";

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
  const [readiness, setReadiness] = useState<Readiness | null>(null);
  const [projects, setProjects] = useState<ProjectRecord[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [tasks, setTasks] = useState<CoreTask[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [evidence, setEvidence] = useState<EvidenceRecord[]>([]);
  const [taskDiff, setTaskDiff] = useState<TaskDiff | null>(null);
  const [agent, setAgent] = useState<string>("");
  const [activeTab, setActiveTab] = useState<ActiveTab>("summary");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refreshReadiness = async () => {
    const value = await coreRequest<Readiness>({ command: "readiness" });
    setReadiness(value);
    if (!agent && value.recommended_agent) setAgent(value.recommended_agent);
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
      refreshReadiness(),
      refreshProjects(),
      refreshTasks(),
    ])
      .then(([capabilities]) => setCaps(capabilities))
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
  const availableAgents = useMemo(
    () => readiness?.tools.filter((tool) => agentIds.has(tool.id) && tool.available) ?? [],
    [readiness],
  );
  const selectedState = selected ? stateMap[selected.state] ?? "PLAN" : "PLAN";
  const canReadDiff = Boolean(
    selected && !["draft", "planned"].includes(selected.state),
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
    if (!selected || !canReadDiff) {
      setTaskDiff(null);
      return;
    }
    coreRequest<TaskDiff>({ command: "task.diff", task_id: selected.task_id })
      .then(setTaskDiff)
      .catch(() => setTaskDiff(null));
  }, [selectedId, selected?.state, canReadDiff]);

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

  const createTask = () =>
    run("create", async () => {
      const title = window.prompt("Divan ne yapsın?");
      if (!title?.trim()) return;
      const created = await coreRequest<CoreTask>({
        command: "task.create",
        title: title.trim(),
        project_id: selectedProject?.project_id ?? undefined,
        engine_id: readiness?.recommended_engine ?? undefined,
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
      const confirmed = window.confirm(
        `Divan bu görevi izole bir Git worktree içinde çalıştıracak.\n\nGörev: ${selected.title}\nAjan: ${agent || "otomatik"}\nMotor: ${readiness?.recommended_engine ?? "otomatik"}\n\nBir kez çalıştırmayı onaylıyor musun?`,
      );
      if (!confirmed) return;
      await coreRequest<CoreTask>({
        command: "task.start",
        task_id: selected.task_id,
        approve_execution: true,
        agent: agent || undefined,
        engine_id: readiness?.recommended_engine ?? undefined,
        prompt: selected.title,
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

  const apiVersion = caps?.api_version ?? caps?.apiVersion ?? 1;

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="seal">D</span>
          <strong>DİVAN</strong>
        </div>
        <div className="project-pill">{selectedProject?.root ?? "Proje seçilmedi"}</div>
        <div className="engine-pill">
          <span className="dot" />
          {readiness?.recommended_engine
            ? `${readiness.recommended_engine} hazır`
            : "motor aranıyor"}
        </div>
      </header>

      <aside className="sidebar">
        <div>
          <nav>
            <button className="nav-item" onClick={addProject}>Projeler</button>
            <button className="nav-item active" onClick={() => setActiveTab("summary")}>Görevler</button>
            <button className="nav-item" onClick={() => setActiveTab("settings")}>Ajanlar</button>
            <button className="nav-item" onClick={() => setActiveTab("evidence")}>Kanıtlar</button>
            <button
              className="nav-item"
              disabled={!canReadDiff}
              onClick={() => setActiveTab("diff")}
            >
              Değişiklikler
            </button>
            <button className="nav-item" disabled>Sürümler</button>
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
        {activeTab === "settings" ? (
          <Settings readiness={readiness} agent={agent} setAgent={setAgent} />
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
                        <span>{task.engine_id ?? "Motor bekliyor"}</span>
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
                      disabled={!canReadDiff}
                      onClick={() => setActiveTab("diff")}
                    >
                      Diff
                    </button>
                    <button disabled>Terminal</button>
                  </div>
                  <div className="summary-grid">
                    <div>
                      <span className="eyebrow">EXECUTION ENGINE</span>
                      <strong>{selected.engine_id ?? readiness?.recommended_engine ?? "bekliyor"}</strong>
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
                      <span className="eyebrow">DIVAN CORE</span>
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
                      <button className="primary" onClick={startTask} disabled={busy !== null}>
                        {busy === "start" ? "Ajan çalışıyor…" : "Çalıştır"}
                      </button>
                    )}
                    {(selected.state === "running" || selected.state === "review") && (
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
            "Bir görev oluşturduğunda burada gerçek Core durumu ve kanıtları görünecek."}
        </p>
        <dl>
          <div><dt>Durum</dt><dd>{selected?.state ?? "—"}</dd></div>
          <div><dt>Engine</dt><dd>{selected?.engine_id ?? readiness?.recommended_engine ?? "—"}</dd></div>
          <div><dt>Ajan</dt><dd>{agent || readiness?.recommended_agent || "—"}</dd></div>
          <div><dt>Kanıt</dt><dd>{evidence.length}</dd></div>
          <div><dt>Mandate</dt><dd>{selected?.mandate_id ? "Var" : "Gerekli"}</dd></div>
        </dl>
        <button
          className="secondary"
          disabled={!canReadDiff}
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
    </main>
  );
}

function Settings({
  readiness,
  agent,
  setAgent,
}: {
  readiness: Readiness | null;
  agent: string;
  setAgent: (value: string) => void;
}) {
  const agents = readiness?.tools.filter((tool) => agentIds.has(tool.id) && tool.available) ?? [];
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
    if (tool.auth_detail === "api-key-env") return "API env ile bağlı";
    return "Bağlı";
  }
  if (tool.auth === "not-connected") return "Giriş gerekli";
  return tool.subscription_supported ? "İlk kullanımda kontrol" : "Bilinmiyor";
}

export default App;