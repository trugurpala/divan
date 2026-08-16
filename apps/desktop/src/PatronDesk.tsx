import { useEffect, useMemo, useState, type ReactNode } from "react";
import { invoke } from "@tauri-apps/api/core";
import { open } from "@tauri-apps/plugin-dialog";

import type { Depth } from "./DoctorPanel";

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

type GoalSummary = {
  route_id: string | null;
  workflow: string | null;
  workflows: string[];
  roles: string[];
  frameworks: string[];
  project_types: string[];
  task_count: number;
  workstream_count: number;
  sefer_count: number;
  lane: string | null;
  max_parallel_workstreams: number | null;
  required_evidence: string[];
};

type GoalPreview = {
  project_root: string;
  intent: string;
  target: string;
  summary: GoalSummary;
  writes: string[];
  execution_authority: string;
};

type WorkPackageSummary = {
  task_count: number;
  ready_task_ids: string[];
  max_parallel_workstreams: number | null;
  execution_authority: string;
};

type CreatedGoal = {
  goal: { goal_id: string; status: string };
  summary: GoalSummary;
  work_packages: WorkPackageSummary;
  execution_authority: string;
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

function roleLabel(role: string) {
  return role
    .replaceAll("_", " ")
    .replaceAll("-", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

/**
 * The Patron Masası body: project, ferman, plan preview, agency readiness.
 *
 * Rendered inline as the TAHT screen and inside the Ctrl+K dialog alike, so
 * there is one desk and not two. Everything shown comes from Core commands
 * (`project.list`, `readiness`, `goal.preview`, `goal.create`); the panel
 * computes no plan and grants no execution authority of its own.
 */
export function PatronDeskPanel({
  depth = "padisah",
  projectId,
  onOpenWorkPackages,
}: {
  /** Padişah hides file paths; Divan and Teknik show them. */
  depth?: Depth;
  /** The shell's selected project, so the desk and the sidebar agree. */
  projectId?: string | null;
  /** Where "İş paketlerini aç" goes; defaults to a full reload. */
  onOpenWorkPackages?: () => void;
}) {
  const [projects, setProjects] = useState<ProjectRecord[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [readiness, setReadiness] = useState<Readiness | null>(null);
  const [goal, setGoal] = useState("");
  const [preview, setPreview] = useState<GoalPreview | null>(null);
  const [createdGoal, setCreatedGoal] = useState<CreatedGoal | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
      setSelectedProjectId(
        (current) => current || projectId || projectRows[0]?.project_id || "",
      );
    } catch (value) {
      setError(friendlyError(value));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadDesk();
  }, []);

  useEffect(() => {
    if (projectId) setSelectedProjectId(projectId);
  }, [projectId]);

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
  const canPreview = Boolean(selectedProject && goal.trim().length >= 8 && !busy);
  const canSavePlan = Boolean(preview && selectedProject && !busy);

  const resetPlan = () => {
    setPreview(null);
    setCreatedGoal(null);
    setError(null);
  };

  const changeGoal = (value: string) => {
    setGoal(value);
    resetPlan();
  };

  const changeProject = (projectId: string) => {
    setSelectedProjectId(projectId);
    resetPlan();
  };

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
      changeProject(project.project_id);
    } catch (value) {
      setError(friendlyError(value));
    } finally {
      setBusy(false);
    }
  };

  const previewPlan = async () => {
    if (!canPreview || !selectedProject) return;
    setBusy(true);
    setError(null);
    setCreatedGoal(null);
    try {
      const result = await coreRequest<GoalPreview>({
        command: "goal.preview",
        project_id: selectedProject.project_id,
        intent: goal.trim(),
      });
      setPreview(result);
    } catch (value) {
      setError(friendlyError(value));
    } finally {
      setBusy(false);
    }
  };

  const savePlan = async () => {
    if (!canSavePlan || !selectedProject) return;
    setBusy(true);
    setError(null);
    try {
      const result = await coreRequest<CreatedGoal>({
        command: "goal.create",
        project_id: selectedProject.project_id,
        intent: goal.trim(),
        approve_plan_write: true,
      });
      setCreatedGoal(result);
    } catch (value) {
      setError(friendlyError(value));
    } finally {
      setBusy(false);
    }
  };

  const openWorkPackages = onOpenWorkPackages ?? (() => window.location.reload());

  if (loading) {
    return <div className="patron-loading">Ajans durumu okunuyor…</div>;
  }

  return (
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
            onChange={(event) => changeProject(event.target.value)}
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
        {selectedProject && depth !== "padisah" && (
          <code className="patron-path">{selectedProject.root}</code>
        )}
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
          onChange={(event) => changeGoal(event.target.value)}
          placeholder="Örnek: Bu projeyi baştan sona incele. Eksikleri bul, kullanıcı dostu hale getir, testleri geçir ve çalışan teslim adayı hazırla."
          rows={6}
          autoFocus
        />
        <div className="patron-hints">
          <button
            type="button"
            onClick={() =>
              changeGoal(
                "Projeyi incele, mevcut mimariyi koru, eksikleri tamamla, kullanıcı deneyimini iyileştir, testleri ve build'i geçir, kanıtlı teslim adayı hazırla.",
              )
            }
          >
            Anahtar teslim
          </button>
          <button
            type="button"
            onClick={() =>
              changeGoal(
                "Bu hatayı kök nedenine kadar incele, en küçük güvenli düzeltmeyi uygula, regresyon testi ekle ve doğrulama kanıtını hazırla.",
              )
            }
          >
            Hata çöz
          </button>
          <button
            type="button"
            onClick={() =>
              changeGoal(
                "Bu özelliği mevcut mimariye uygun şekilde ekle, kullanıcı akışını sade tut, güvenlik ve kalite kapılarını koru, test ederek teslim et.",
              )
            }
          >
            Özellik ekle
          </button>
        </div>
      </section>

      {preview && (
        <section className="patron-block patron-plan" aria-live="polite">
          <div className="patron-block-title">
            <span>3</span>
            <div>
              <strong>Plan önizlemesi</strong>
              <small>Salt okunur hesaplandı; henüz proje dosyası yazılmadı.</small>
            </div>
          </div>
          <div className="patron-plan-grid">
            <article><strong>{preview.summary.task_count}</strong><small>İş paketi</small></article>
            <article><strong>{preview.summary.workstream_count}</strong><small>İş akışı</small></article>
            <article><strong>{preview.summary.sefer_count}</strong><small>Sefer</small></article>
            <article>
              <strong>{preview.summary.max_parallel_workstreams ?? 1}</strong>
              <small>En fazla paralel</small>
            </article>
          </div>
          <div className="patron-role-row">
            {preview.summary.roles.slice(0, 8).map((role) => (
              <span key={role}>{roleLabel(role)}</span>
            ))}
          </div>
          <p className="patron-readiness-copy">
            {preview.summary.required_evidence.length} kanıt yükümlülüğü · çalışma modeli:{" "}
            {preview.summary.lane === "bounded-parallel" ? "kontrollü paralel" : "sıralı"}.
          </p>
        </section>
      )}

      <section className="patron-block">
        <div className="patron-block-title">
          <span>{preview ? "4" : "3"}</span>
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
            : "Henüz ana ajan bulunamadı. Plan hazırlanabilir; kod çalışması ajan hazır olana kadar başlatılmaz."}
        </p>
      </section>

      {error && <div className="patron-error">{error}</div>}

      {createdGoal ? (
        <section className="patron-success" aria-live="polite">
          <span>✓</span>
          <div>
            <strong>
              Plan kaydedildi · {createdGoal.work_packages.task_count} iş paketi hazır
            </strong>
            <p>
              {createdGoal.work_packages.ready_task_ids.length} iş paketi başlangıca hazır.
              Henüz kaynak kod değiştirilmedi; çalışma için ayrıca açık onay gerekir.
            </p>
          </div>
          <button type="button" onClick={openWorkPackages}>İş paketlerini aç</button>
        </section>
      ) : (
        <footer className="patron-actions">
          <div>
            <strong>{selectedProject ? selectedProject.name : "Proje bekleniyor"}</strong>
            <small>
              {!preview
                ? "Önce salt-okunur planı çıkar; hiçbir şey yazılmaz."
                : "Planı kaydetmek yalnız plan ve yerel iş paketi durumunu yazar; kod çalıştırmaz."}
            </small>
          </div>
          {!preview ? (
            <button type="button" onClick={previewPlan} disabled={!canPreview}>
              {busy ? "Planlanıyor…" : "Planı önizle →"}
            </button>
          ) : (
            <button type="button" onClick={savePlan} disabled={!canSavePlan}>
              {busy ? "Kaydediliyor…" : "Planı kaydet →"}
            </button>
          )}
        </footer>
      )}
    </div>
  );
}

/**
 * The Ctrl+K quick desk. It wraps the same panel the TAHT screen shows, so
 * the dialog is a shortcut to the desk and never a second desk.
 */
export default function PatronDesk({
  children = null,
  depth = "padisah",
}: {
  children?: ReactNode;
  depth?: Depth;
}) {
  const [openDesk, setOpenDesk] = useState(false);

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
                  Önce gerçek planı gör. Planı kaydettiğinde Divan iş paketlerini hazırlar;
                  kaynak kodu değiştirecek çalışma yine ayrı açık onay ister.
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
            <PatronDeskPanel depth={depth} />
          </section>
        </div>
      )}
    </>
  );
}
