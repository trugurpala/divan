import { useEffect, useMemo, useState, type ReactNode } from "react";
import { invoke } from "@tauri-apps/api/core";
import { open } from "@tauri-apps/plugin-dialog";

type CoreEnvelope<T> = {
  api_version: number;
  ok: boolean;
  result?: T;
  error?: { code: string; message: string };
};

type ProjectRecord = {
  project_id: string;
  name: string;
  root: string;
  created_at: string;
  last_opened_at: string;
};

type ToolStatus = {
  id: string;
  display_name: string;
  available: boolean;
  auth: string;
  auth_detail: string | null;
};

type Readiness = {
  ready: boolean;
  tools: ToolStatus[];
  recommended_agent: string | null;
};

type CoreTask = {
  task_id: string;
  title: string;
  state: string;
};

const primaryAgents = ["codex", "claude", "cursor-agent"] as const;

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

function toolLabel(id: string) {
  if (id === "codex") return "Codex";
  if (id === "claude") return "Claude Code";
  if (id === "cursor-agent") return "Cursor Agent";
  return id;
}

function connectionLabel(tool: ToolStatus | undefined) {
  if (!tool?.available) return "Bulunamadı";
  if (tool.auth === "connected") return "Hazır";
  if (tool.auth === "not-connected") return "Giriş gerekli";
  return "Kurulu";
}

function friendlyError(value: unknown) {
  const message = String(value);
  const marker = "Error: ";
  return message.startsWith(marker) ? message.slice(marker.length) : message;
}

export default function PatronDesk({ children }: { children: ReactNode }) {
  const [openDesk, setOpenDesk] = useState(false);
  const [projects, setProjects] = useState<ProjectRecord[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [readiness, setReadiness] = useState<Readiness | null>(null);
  const [goal, setGoal] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createdTask, setCreatedTask] = useState<CoreTask | null>(null);

  const loadDesk = async () => {
    setLoading(true);
    setError(null);
    try {
      const [projectRows, ready] = await Promise.all([
        coreRequest<ProjectRecord[]>({ command: "project.list" }),
        coreRequest<Readiness>({ command: "readiness" }),
      ]);
      setProjects(projectRows);
      setReadiness(ready);
      setSelectedProjectId((current) => current || projectRows[0]?.project_id || "");
    } catch (value) {
      setError(friendlyError(value));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const commandKey = event.ctrlKey || event.metaKey;
      if (commandKey && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpenDesk(true);
      }
      if (event.key === "Escape") setOpenDesk(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  useEffect(() => {
    if (openDesk) void loadDesk();
  }, [openDesk]);

  const selectedProject = useMemo(
    () => projects.find((project) => project.project_id === selectedProjectId) ?? null,
    [projects, selectedProjectId],
  );

  const agentRows = useMemo(
    () =>
      primaryAgents.map((id) => ({
        id,
        tool: readiness?.tools.find((candidate) => candidate.id === id),
      })),
    [readiness],
  );

  const availableAgentCount = agentRows.filter((row) => row.tool?.available).length;
  const canCreate = Boolean(selectedProject && goal.trim().length >= 8 && !busy);

  const addProject = async () => {
    setError(null);
    const folder = await open({
      directory: true,
      multiple: false,
      title: "Divan'ın çalışacağı Git proje klasörünü seç",
    });
    if (typeof folder !== "string" || !folder.trim()) return;
    setBusy(true);
    try {
      const project = await coreRequest<ProjectRecord>({
        command: "project.register",
        root: folder.trim(),
      });
      const rows = await coreRequest<ProjectRecord[]>({ command: "project.list" });
      setProjects(rows);
      setSelectedProjectId(project.project_id);
    } catch (value) {
      setError(friendlyError(value));
    } finally {
      setBusy(false);
    }
  };

  const createMandate = async () => {
    if (!canCreate || !selectedProject) return;
    setBusy(true);
    setError(null);
    setCreatedTask(null);
    try {
      const created = await coreRequest<CoreTask>({
        command: "task.create",
        title: goal.trim(),
        project_id: selectedProject.project_id,
      });
      const planned = await coreRequest<CoreTask>({
        command: "task.plan",
        task_id: created.task_id,
        reason: "Patron Masası: kullanıcı hedefinden plan oluştur",
      });
      setCreatedTask(planned);
    } catch (value) {
      setError(friendlyError(value));
    } finally {
      setBusy(false);
    }
  };

  const refreshApp = () => window.location.reload();

  return (
    <>
      {children}
      <button
        type="button"
        className="patron-launcher"
        onClick={() => setOpenDesk(true)}
        aria-haspopup="dialog"
        aria-expanded={openDesk}
      >
        <span className="patron-launcher-mark">✦</span>
        <span>
          <strong>Patron Masası</strong>
          <small>Ferman ver · Ctrl+K</small>
        </span>
      </button>

      {openDesk && (
        <div className="patron-backdrop" onMouseDown={() => setOpenDesk(false)}>
          <section
            className="patron-desk"
            role="dialog"
            aria-modal="true"
            aria-labelledby="patron-desk-title"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <header className="patron-desk-header">
              <div>
                <span className="patron-kicker">TEK YERDEN YÖNET</span>
                <h1 id="patron-desk-title">Ne yapılacağını söyle.</h1>
                <p>
                  Divan görevi kaydeder ve planlar. Kaynak koda dokunacak çalışma ise yine ayrı
                  açık onay ister.
                </p>
              </div>
              <button
                type="button"
                className="patron-close"
                onClick={() => setOpenDesk(false)}
                aria-label="Patron Masası'nı kapat"
              >
                ×
              </button>
            </header>

            {loading ? (
              <div className="patron-loading">Ajans durumu okunuyor…</div>
            ) : (
              <div className="patron-body">
                <section className="patron-block">
                  <div className="patron-block-title">
                    <span>1</span>
                    <div>
                      <strong>Proje</strong>
                      <small>Divan yalnız seçtiğin Git klasöründe çalışır.</small>
                    </div>
                  </div>
                  <div className="patron-project-row">
                    <select
                      value={selectedProjectId}
                      onChange={(event) => setSelectedProjectId(event.target.value)}
                      aria-label="Çalışılacak proje"
                    >
                      <option value="">Proje seç</option>
                      {projects.map((project) => (
                        <option value={project.project_id} key={project.project_id}>
                          {project.name}
                        </option>
                      ))}
                    </select>
                    <button type="button" onClick={addProject} disabled={busy}>
                      + Klasör ekle
                    </button>
                  </div>
                  {selectedProject && <code className="patron-path">{selectedProject.root}</code>}
                </section>

                <section className="patron-block">
                  <div className="patron-block-title">
                    <span>2</span>
                    <div>
                      <strong>Ferman</strong>
                      <small>Teknik ayrıntı yazmak zorunda değilsin; sonucu tarif et.</small>
                    </div>
                  </div>
                  <textarea
                    value={goal}
                    onChange={(event) => setGoal(event.target.value)}
                    placeholder="Örnek: Bu projeyi baştan sona incele. Eksikleri bul, kullanıcı dostu hale getir, testleri geçir ve çalışan teslim adayı hazırla."
                    rows={6}
                    autoFocus
                  />
                  <div className="patron-hints">
                    <button
                      type="button"
                      onClick={() =>
                        setGoal(
                          "Projeyi incele, mevcut mimariyi koru, eksikleri tamamla, kullanıcı deneyimini iyileştir, testleri ve build'i geçir, kanıtlı teslim adayı hazırla.",
                        )
                      }
                    >
                      Anahtar teslim
                    </button>
                    <button
                      type="button"
                      onClick={() =>
                        setGoal(
                          "Bu hatayı kök nedenine kadar incele, en küçük güvenli düzeltmeyi uygula, regresyon testi ekle ve doğrulama kanıtını hazırla.",
                        )
                      }
                    >
                      Hata çöz
                    </button>
                    <button
                      type="button"
                      onClick={() =>
                        setGoal(
                          "Bu özelliği mevcut mimariye uygun şekilde ekle, kullanıcı akışını sade tut, güvenlik ve kalite kapılarını koru, test ederek teslim et.",
                        )
                      }
                    >
                      Özellik ekle
                    </button>
                  </div>
                </section>

                <section className="patron-block">
                  <div className="patron-block-title">
                    <span>3</span>
                    <div>
                      <strong>Ajans hazırlığı</strong>
                      <small>Kurulu abonelik/oturumlar kullanılır; kimlik bilgisi kopyalanmaz.</small>
                    </div>
                  </div>
                  <div className="patron-agents">
                    {agentRows.map(({ id, tool }) => (
                      <article key={id} className={tool?.available ? "ready" : "missing"}>
                        <div className="patron-agent-dot" />
                        <strong>{tool?.display_name || toolLabel(id)}</strong>
                        <small>{connectionLabel(tool)}</small>
                      </article>
                    ))}
                  </div>
                  <p className="patron-readiness-copy">
                    {availableAgentCount > 0
                      ? `${availableAgentCount}/3 ana ajan bulundu. Divan çalışma anında yalnız kullanılabilir ajanı seçer.`
                      : "Henüz ana ajan bulunamadı. Ferman planlanabilir; execution ajan hazır olana kadar başlatılmaz."}
                  </p>
                </section>

                {error && <div className="patron-error">{error}</div>}

                {createdTask ? (
                  <section className="patron-success" aria-live="polite">
                    <span>✓</span>
                    <div>
                      <strong>Ferman planlandı: {createdTask.task_id}</strong>
                      <p>
                        Henüz kaynak kod değiştirilmedi. Görev ekranında çalışma ayrıntılarını görüp
                        execution için tek seferlik onay verebilirsin.
                      </p>
                    </div>
                    <button type="button" onClick={refreshApp}>Göreve git</button>
                  </section>
                ) : (
                  <footer className="patron-actions">
                    <div>
                      <strong>{selectedProject ? selectedProject.name : "Proje bekleniyor"}</strong>
                      <small>
                        {goal.trim().length < 8
                          ? "Hedefi normal Türkçe ile yaz."
                          : "Hazır: önce plan oluşturulacak, execution ayrı onay isteyecek."}
                      </small>
                    </div>
                    <button type="button" onClick={createMandate} disabled={!canCreate}>
                      {busy ? "Hazırlanıyor…" : "Fermanı hazırla →"}
                    </button>
                  </footer>
                )}
              </div>
            )}
          </section>
        </div>
      )}
    </>
  );
}
